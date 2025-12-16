#!/usr/bin/env python3
"""Test predefined filters feature."""

from nodi.config.loader import ConfigLoader
import tempfile
import os

# Create a test config with predefined filters
test_config_yaml = """
services:
  testapi:
    dev:
      base_url: https://jsonplaceholder.typicode.com
    aliases:
      posts: /posts
      users: /users
default_environment: dev
default_service: testapi

# Predefined filters
filters:
  emails: ".[*].email"
  ids: ".[*].id"
  user_ids: ".[*].userId"
  titles: ".[*].title"
  count: "length"
  first: ".[0]"
  first_title: ".[0].title"
  names: ".[*].name"
"""

# Write test config to temp file
with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
    f.write(test_config_yaml)
    temp_config_path = f.name

try:
    # Load the test config
    loader = ConfigLoader()
    config = loader.load(temp_config_path)

    print("Testing Predefined Filters Feature:")
    print("="*70)

    # Test 1: List filters
    print("\nTest 1: List all predefined filters")
    print("-" * 70)
    filters = config.list_filters()
    print(f"Found {len(filters)} predefined filters:")
    for name, expression in filters.items():
        print(f"  @{name}: {expression}")

    # Test 2: Get specific filter
    print("\nTest 2: Get specific filter by name")
    print("-" * 70)
    test_cases = [
        ("emails", ".[*].email"),
        ("ids", ".[*].id"),
        ("count", "length"),
        ("first_title", ".[0].title"),
    ]

    for filter_name, expected_expr in test_cases:
        actual_expr = config.get_filter(filter_name)
        status = "PASS" if actual_expr == expected_expr else "FAIL"
        print(f"  Filter '{filter_name}': {actual_expr} [{status}]")

    # Test 3: Non-existent filter
    print("\nTest 3: Request non-existent filter")
    print("-" * 70)
    result = config.get_filter("nonexistent")
    status = "PASS" if result is None else "FAIL"
    print(f"  get_filter('nonexistent'): {result} [{status}]")

    # Test 4: Simulate filter resolution (what REPL does)
    print("\nTest 4: Simulate REPL filter resolution")
    print("-" * 70)

    def resolve_filter(filter_expr: str, config) -> str:
        """Simulate REPL filter resolution."""
        if filter_expr.startswith("@"):
            filter_name = filter_expr[1:].strip()
            predefined = config.get_filter(filter_name)
            if predefined:
                return predefined
            else:
                return filter_expr  # Not found, return original
        return filter_expr

    resolution_tests = [
        ("@emails", ".[*].email", "Resolve @emails"),
        ("@count", "length", "Resolve @count"),
        (".[*].name", ".[*].name", "Direct expression (no @)"),
        ("@nonexistent", "@nonexistent", "Non-existent filter"),
    ]

    for input_filter, expected_output, description in resolution_tests:
        result = resolve_filter(input_filter, config)
        status = "PASS" if result == expected_output else "FAIL"
        print(f"  {description}")
        print(f"    Input:    {input_filter}")
        print(f"    Output:   {result}")
        print(f"    Expected: {expected_output}")
        print(f"    Status:   {status}")

    print("\n" + "="*70)
    print("All tests completed!")

finally:
    # Clean up temp file
    os.unlink(temp_config_path)
