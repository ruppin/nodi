#!/usr/bin/env python3
"""Integration test for predefined filters with actual filter application."""

from nodi.config.loader import ConfigLoader
from nodi.filters import JSONFilter
import tempfile
import os

# Create a test config with predefined filters
test_config_yaml = """
services:
  testapi:
    dev:
      base_url: https://api.example.com
    aliases:
      users: /users
default_environment: dev
default_service: testapi

filters:
  emails: ".[*].email"
  ids: ".[*].id"
  count: "length"
  first: ".[0]"
  first_email: ".[0].email"
"""

# Sample API response data
sample_users = [
    {"id": 1, "name": "John", "email": "john@example.com"},
    {"id": 2, "name": "Jane", "email": "jane@example.com"},
    {"id": 3, "name": "Bob", "email": "bob@example.com"},
]

# Write test config to temp file
with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
    f.write(test_config_yaml)
    temp_config_path = f.name

try:
    # Load the test config
    loader = ConfigLoader()
    config = loader.load(temp_config_path)

    # Create JSON filter
    json_filter = JSONFilter()

    print("Integration Test: Predefined Filters + Filter Application:")
    print("="*70)

    print("\nSample Data:")
    print("-" * 70)
    import json
    print(json.dumps(sample_users, indent=2))

    # Test cases: (filter_name, expected_result, description)
    test_cases = [
        ("emails", ["john@example.com", "jane@example.com", "bob@example.com"], "Extract all emails"),
        ("ids", [1, 2, 3], "Extract all IDs"),
        ("count", 3, "Count users"),
        ("first", {"id": 1, "name": "John", "email": "john@example.com"}, "Get first user"),
        ("first_email", "john@example.com", "Get first user's email"),
    ]

    print("\n" + "="*70)
    print("Test Results:")
    print("="*70)

    for filter_name, expected_result, description in test_cases:
        print(f"\nTest: {description}")
        print("-" * 70)

        # Simulate REPL: resolve filter name to expression
        filter_expr = config.get_filter(filter_name)
        print(f"  Filter name:   @{filter_name}")
        print(f"  Filter expr:   {filter_expr}")

        # Apply the filter to sample data
        try:
            result = json_filter.apply(sample_users, filter_expr)
            print(f"  Result:        {json.dumps(result) if isinstance(result, (list, dict)) else result}")
            print(f"  Expected:      {json.dumps(expected_result) if isinstance(expected_result, (list, dict)) else expected_result}")

            # Compare results
            if result == expected_result:
                print(f"  Status:        PASS")
            else:
                print(f"  Status:        FAIL - Results don't match!")

        except Exception as e:
            print(f"  ERROR: {e}")
            print(f"  Status:        FAIL")

    # Demonstrate workflow: filter resolution + application
    print("\n" + "="*70)
    print("Simulated REPL Workflow:")
    print("="*70)

    def simulate_repl_request(endpoint: str, filter_spec: str, data, config):
        """Simulate a complete REPL request with filter."""
        print(f"\nCommand: {endpoint} | {filter_spec}")
        print("-" * 70)

        # Resolve filter if it's a predefined one
        if filter_spec.startswith("@"):
            filter_name = filter_spec[1:]
            filter_expr = config.get_filter(filter_name)
            if filter_expr:
                print(f"  Resolved @{filter_name} -> {filter_expr}")
            else:
                print(f"  Warning: Filter '@{filter_name}' not found")
                filter_expr = filter_spec
        else:
            filter_expr = filter_spec

        # Apply filter
        json_filter = JSONFilter()
        result = json_filter.apply(data, filter_expr)
        print(f"  Result: {json.dumps(result) if isinstance(result, (list, dict)) else result}")

        return result

    # Simulate various REPL commands
    simulate_repl_request("users", "@emails", sample_users, config)
    simulate_repl_request("users", "@count", sample_users, config)
    simulate_repl_request("users", ".[*].name", sample_users, config)  # Direct expression
    simulate_repl_request("users", "@first_email", sample_users, config)

    print("\n" + "="*70)
    print("All integration tests completed!")
    print("="*70)

finally:
    # Clean up temp file
    os.unlink(temp_config_path)
