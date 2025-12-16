#!/usr/bin/env python3
"""
Comprehensive test suite for Nodi scripting system.
Tests parser, engine, suite runner, and integration.
"""

import sys
import os
from pathlib import Path

# Add nodi to path
sys.path.insert(0, str(Path(__file__).parent))

from nodi.scripting import ScriptParser, ScriptEngine, SuiteRunner
from nodi.config.loader import ConfigLoader
from nodi.providers.rest import RestProvider
from nodi.environment.resolver import URLResolver
from nodi.config.models import Config


def test_parser():
    """Test script parser."""
    print("=" * 70)
    print("TEST 1: Script Parser")
    print("=" * 70)

    parser = ScriptParser()

    # Test script
    script = """
# Test script
$user_id = 123
$name = "John"

# HTTP request
GET users
GET user:$user_id | @emails

# Assertions
assert $user_id == 123
assert $name != null

# Output
echo "Test message"
print $user_id
"""

    lines = parser.parse(script)

    print(f"Parsed {len(lines)} lines:")
    for line in lines:
        print(f"  Line {line.line_number}: {line.line_type} - {line.content}")

    # Validate
    assert len(lines) > 0, "Should parse multiple lines"
    assert any(l.line_type == 'assignment' for l in lines), "Should have assignments"
    assert any(l.line_type == 'http' for l in lines), "Should have HTTP requests"
    assert any(l.line_type == 'assert' for l in lines), "Should have assertions"
    assert any(l.line_type == 'echo' for l in lines), "Should have echo statements"

    print("[PASS] Parser test\n")


def test_engine_basic():
    """Test script engine with basic operations."""
    print("=" * 70)
    print("TEST 2: Script Engine - Basic Operations")
    print("=" * 70)

    # Create a simple test script
    script_path = Path(__file__).parent / "test_script_temp.nodi"
    script_content = """
# Basic script test
$x = 10
$y = 20

echo "Testing basic operations"
print $x

assert $x == 10
assert $y > 15

echo "All assertions passed"
"""

    script_path.write_text(script_content)

    try:
        # Load config
        config_file = Path(__file__).parent / "config.yml"
        if not config_file.exists():
            print("[WARN] Config file not found, skipping engine test")
            return

        loader = ConfigLoader(str(config_file))
        config = loader.load()

        # Create engine
        rest_provider = RestProvider()
        resolver = URLResolver(config.services, config.environments)
        engine = ScriptEngine(config, rest_provider, resolver)

        # Run script
        result = engine.run_script(str(script_path))

        print(f"Status: {result['status']}")
        print(f"Duration: {result['duration']:.3f}s")
        print(f"Output:")
        for line in result.get('output', []):
            print(f"  {line}")

        assert result['status'] == 'PASS', f"Script should pass, got {result.get('error', '')}"
        print("[PASS]Engine basic test PASSED\n")

    finally:
        # Cleanup
        if script_path.exists():
            script_path.unlink()


def test_engine_with_parameters():
    """Test script engine with parameters."""
    print("=" * 70)
    print("TEST 3: Script Engine - With Parameters")
    print("=" * 70)

    script_path = Path(__file__).parent / "test_params_temp.nodi"
    script_content = """
# Parameter test
echo "User ID: $user_id"
echo "Name: $name"

assert $user_id == 123
assert $name == "John"

print $user_id
"""

    script_path.write_text(script_content)

    try:
        config_file = Path(__file__).parent / "config.yml"
        if not config_file.exists():
            print("[WARN] Config file not found, skipping parameter test")
            return

        loader = ConfigLoader(str(config_file))
        config = loader.load()

        rest_provider = RestProvider()
        resolver = URLResolver(config.services, config.environments)
        engine = ScriptEngine(config, rest_provider, resolver)

        # Run with parameters
        params = {'user_id': 123, 'name': 'John'}
        result = engine.run_script(str(script_path), params)

        print(f"Status: {result['status']}")
        print(f"Output:")
        for line in result.get('output', []):
            print(f"  {line}")

        assert result['status'] == 'PASS', f"Script should pass, got {result.get('error', '')}"
        print("[PASS]Engine parameter test PASSED\n")

    finally:
        if script_path.exists():
            script_path.unlink()


def test_suite_runner():
    """Test suite runner with sequential scripts."""
    print("=" * 70)
    print("TEST 4: Suite Runner - Sequential")
    print("=" * 70)

    # Create test scripts
    script_dir = Path(__file__).parent / "test_scripts_temp"
    script_dir.mkdir(exist_ok=True)

    script1 = script_dir / "test1.nodi"
    script1.write_text("""
echo "Running test 1"
$x = 1
assert $x == 1
""")

    script2 = script_dir / "test2.nodi"
    script2.write_text("""
echo "Running test 2"
$y = 2
assert $y == 2
""")

    # Create suite file
    suite_file = script_dir / "test_suite.yml"
    suite_file.write_text("""
name: Test Suite
scripts:
  - test1.nodi
  - test2.nodi

options:
  stop_on_error: true
""")

    try:
        config_file = Path(__file__).parent / "config.yml"
        if not config_file.exists():
            print("[WARN] Config file not found, skipping suite test")
            return

        loader = ConfigLoader(str(config_file))
        config = loader.load()

        rest_provider = RestProvider()
        resolver = URLResolver(config.services, config.environments)
        engine = ScriptEngine(config, rest_provider, resolver)
        suite_runner = SuiteRunner(engine)

        # Run suite
        results = suite_runner.run_suite(str(suite_file))

        print(f"Suite: {results['suite']}")
        print(f"Total: {results['total']}")
        print(f"Passed: {results['passed']}")
        print(f"Failed: {results['failed']}")
        print(f"Duration: {results['duration']:.3f}s")

        for step in results['steps']:
            print(f"  [{step['status']}] {step['script']}")

        assert results['passed'] == 2, "Both scripts should pass"
        assert results['failed'] == 0, "No scripts should fail"
        print("[PASS]Suite runner test PASSED\n")

    finally:
        # Cleanup
        for f in script_dir.glob("*"):
            f.unlink()
        script_dir.rmdir()


def test_parallel_execution():
    """Test parallel script execution."""
    print("=" * 70)
    print("TEST 5: Parallel Execution")
    print("=" * 70)

    script_dir = Path(__file__).parent / "test_parallel_temp"
    script_dir.mkdir(exist_ok=True)

    # Create test scripts
    for i in range(1, 4):
        script = script_dir / f"test{i}.nodi"
        script.write_text(f"""
echo "Running test {i}"
$x = {i}
assert $x == {i}
""")

    try:
        config_file = Path(__file__).parent / "config.yml"
        if not config_file.exists():
            print("[WARN] Config file not found, skipping parallel test")
            return

        loader = ConfigLoader(str(config_file))
        config = loader.load()

        rest_provider = RestProvider()
        resolver = URLResolver(config.services, config.environments)
        engine = ScriptEngine(config, rest_provider, resolver)
        suite_runner = SuiteRunner(engine)

        # Run in parallel
        script_paths = [str(script_dir / f"test{i}.nodi") for i in range(1, 4)]
        results = suite_runner.run_scripts_parallel(script_paths)

        print(f"Total: {results['total']}")
        print(f"Passed: {results['passed']}")
        print(f"Failed: {results['failed']}")
        print(f"Duration: {results['duration']:.3f}s")

        for script_result in results['scripts']:
            print(f"  [{script_result['status']}] {Path(script_result['script']).name}")

        assert results['passed'] == 3, "All scripts should pass"
        assert results['failed'] == 0, "No scripts should fail"
        print("[PASS]Parallel execution test PASSED\n")

    finally:
        # Cleanup
        for f in script_dir.glob("*"):
            f.unlink()
        script_dir.rmdir()


def test_assertion_failure():
    """Test assertion failure handling."""
    print("=" * 70)
    print("TEST 6: Assertion Failure Handling")
    print("=" * 70)

    script_path = Path(__file__).parent / "test_fail_temp.nodi"
    script_content = """
echo "This should fail"
$x = 10
assert $x == 20
echo "This should not execute"
"""

    script_path.write_text(script_content)

    try:
        config_file = Path(__file__).parent / "config.yml"
        if not config_file.exists():
            print("[WARN] Config file not found, skipping failure test")
            return

        loader = ConfigLoader(str(config_file))
        config = loader.load()

        rest_provider = RestProvider()
        resolver = URLResolver(config.services, config.environments)
        engine = ScriptEngine(config, rest_provider, resolver)

        result = engine.run_script(str(script_path))

        print(f"Status: {result['status']}")
        print(f"Error: {result.get('error', 'None')}")

        assert result['status'] == 'FAIL', "Script should fail"
        assert 'Assertion failed' in result.get('error', ''), "Should have assertion error"
        print("[PASS]Assertion failure test PASSED\n")

    finally:
        if script_path.exists():
            script_path.unlink()


def run_all_tests():
    """Run all tests."""
    print("\n")
    print("=" * 70)
    print("NODI SCRIPTING SYSTEM - COMPREHENSIVE TEST SUITE")
    print("=" * 70)
    print("\n")

    tests = [
        ("Parser", test_parser),
        ("Engine Basic", test_engine_basic),
        ("Engine Parameters", test_engine_with_parameters),
        ("Suite Runner", test_suite_runner),
        ("Parallel Execution", test_parallel_execution),
        ("Assertion Failure", test_assertion_failure),
    ]

    passed = 0
    failed = 0

    for name, test_func in tests:
        try:
            test_func()
            passed += 1
        except Exception as e:
            print(f"[FAIL] {name} test FAILED: {e}\n")
            import traceback
            traceback.print_exc()
            failed += 1

    print("\n")
    print("=" * 70)
    print("FINAL RESULTS")
    print("=" * 70)
    print(f"Total: {len(tests)}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print("=" * 70)

    if failed == 0:
        print("\n[PASS] ALL TESTS PASSED!\n")
        return 0
    else:
        print(f"\n[FAIL] {failed} TEST(S) FAILED\n")
        return 1


if __name__ == "__main__":
    sys.exit(run_all_tests())
