#!/usr/bin/env python3
"""Test path parameter substitution."""

from nodi.config.loader import ConfigLoader
from nodi.environment.resolver import URLResolver

# Load config
loader = ConfigLoader()
config = loader.load("c:\\Users\\Motrola\\.nodi\\config.yml")

# Create resolver
resolver = URLResolver(config)

# Test cases
test_cases = [
    ("user:123", "user", "123"),
    ("user:456", "user", "456"),
    ("person:1", "person", "1"),
]

print("Testing path parameter substitution:\n")

for input_str, expected_alias, expected_id in test_cases:
    try:
        # Parse the input
        spec = resolver.parse(input_str, default_service="jsonplaceholder", default_env="dev")

        print(f"Input: {input_str}")
        print(f"  Parsed endpoint: {spec.endpoint}")
        print(f"  Path params: {spec.path_params}")

        # Resolve to URL
        url = resolver.resolve(spec)
        print(f"  Resolved URL: {url}")
        print()

    except Exception as e:
        print(f"Input: {input_str}")
        print(f"  ERROR: {e}")
        print()

print("\n" + "="*50)
print("Testing SWAPI person endpoint:")
print("="*50 + "\n")

# Test with SWAPI
try:
    spec = resolver.parse("person:1", default_service="swapi", default_env="dev")
    print(f"Input: person:1")
    print(f"  Parsed endpoint: {spec.endpoint}")
    print(f"  Path params: {spec.path_params}")

    url = resolver.resolve(spec)
    print(f"  Resolved URL: {url}")
    print(f"  Expected: https://swapi.dev/api/people/1/")

except Exception as e:
    print(f"ERROR: {e}")
