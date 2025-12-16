#!/usr/bin/env python3
"""Test path parameter substitution with special characters."""

from nodi.config.loader import ConfigLoader
from nodi.environment.resolver import URLResolver

# Load config
loader = ConfigLoader()
config = loader.load("c:\\Users\\Motrola\\.nodi\\config.yml")

# Create resolver
resolver = URLResolver(config)

print("Testing path parameters with special characters:")
print("="*60)

# Test cases with different parameter formats
test_cases = [
    ("user:123", "Numeric"),
    ("user:abc-123", "Alphanumeric with hyphen"),
    ("user:user-abc-def-123", "Complex alphanumeric with hyphens"),
    ("user:ABC123", "Uppercase alphanumeric"),
    ("user:test_user_123", "With underscores"),
    ("user:a1b2c3", "Mixed letters and numbers"),
    ("person:luke-skywalker", "SWAPI style ID"),
]

for input_str, description in test_cases:
    print(f"\nTest: {description}")
    print(f"Input: {input_str}")
    print("-" * 60)

    try:
        # Parse the input
        spec = resolver.parse(input_str, default_service="jsonplaceholder", default_env="dev")

        print(f"  Endpoint:    {spec.endpoint}")
        print(f"  Path params: {spec.path_params}")

        # Resolve to URL
        url = resolver.resolve(spec)
        print(f"  Resolved URL: {url}")

        # Verify the parameter is in the URL
        if spec.path_params and 'id' in spec.path_params:
            param_value = spec.path_params['id']
            if param_value in url:
                print(f"  Status: PASS - Parameter '{param_value}' found in URL")
            else:
                print(f"  Status: FAIL - Parameter '{param_value}' NOT found in URL")

    except Exception as e:
        print(f"  ERROR: {e}")
        import traceback
        traceback.print_exc()

print("\n" + "="*60)
print("Testing with SWAPI (handles hyphenated IDs):")
print("="*60)

# SWAPI uses hyphenated IDs like "luke-skywalker"
swapi_tests = [
    "person:1",
    "person:luke-skywalker",
    "person:r2-d2",
]

for test_input in swapi_tests:
    print(f"\nInput: {test_input}")
    print("-" * 60)

    try:
        spec = resolver.parse(test_input, default_service="swapi", default_env="dev")
        url = resolver.resolve(spec)

        print(f"  Endpoint:    {spec.endpoint}")
        print(f"  Path params: {spec.path_params}")
        print(f"  Resolved URL: {url}")

        if spec.path_params and 'id' in spec.path_params:
            param_value = spec.path_params['id']
            if param_value in url:
                print(f"  Status: PASS")
            else:
                print(f"  Status: FAIL")

    except Exception as e:
        print(f"  ERROR: {e}")
