#!/usr/bin/env python3
"""Test script to verify REPL fixes."""

from nodi.config.loader import ConfigLoader
from nodi.environment.manager import EnvironmentManager
from nodi.scripting import ScriptEngine, SuiteRunner
from nodi.providers.rest import RestProvider

def test_components():
    """Test that all components initialize correctly."""
    print("Testing Nodi components...")

    # Load config
    print("[OK] Loading config...")
    config = ConfigLoader().load()

    # Test EnvironmentManager has resolver
    print("[OK] Testing EnvironmentManager...")
    env_mgr = EnvironmentManager(config)
    assert hasattr(env_mgr, 'resolver'), "EnvironmentManager should have resolver attribute"
    assert env_mgr.resolver is not None, "Resolver should not be None"
    print(f"  - resolver attribute exists: {hasattr(env_mgr, 'resolver')}")
    print(f"  - resolver type: {type(env_mgr.resolver).__name__}")

    # Test ScriptEngine initialization
    print("[OK] Testing ScriptEngine...")
    rest_provider = RestProvider()
    script_engine = ScriptEngine(config, rest_provider, env_mgr.resolver)
    print(f"  - ScriptEngine initialized successfully")

    # Test SuiteRunner initialization
    print("[OK] Testing SuiteRunner...")
    suite_runner = SuiteRunner(script_engine)
    print(f"  - SuiteRunner initialized successfully")

    print("\n" + "=" * 60)
    print("ALL TESTS PASSED!")
    print("=" * 60)
    print("\nYou can now run 'nodi repl' from the command line.")

if __name__ == "__main__":
    try:
        test_components()
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
