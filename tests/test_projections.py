#!/usr/bin/env python3
"""Test output projection feature."""

from nodi.projections import JSONProjection
import json

# Sample data
sample_users = [
    {"id": 1, "name": "John", "email": "john@example.com", "phone": "111-111-1111", "address": {"city": "New York"}},
    {"id": 2, "name": "Jane", "email": "jane@example.com", "phone": "222-222-2222", "address": {"city": "LA"}},
    {"id": 3, "name": "Bob", "email": "bob@example.com", "phone": "333-333-3333", "address": {"city": "Chicago"}},
]

print("Testing JSON Projection Feature:")
print("="*70)

projection = JSONProjection()

# Test 1: Simple field list projection
print("\nTest 1: Simple field list projection")
print("-" * 70)
print("Projection: ['id', 'name', 'email']")

result = projection.apply(sample_users, ['id', 'name', 'email'])
print("\nResult:")
print(json.dumps(result, indent=2))

expected = [
    {"id": 1, "name": "John", "email": "john@example.com"},
    {"id": 2, "name": "Jane", "email": "jane@example.com"},
    {"id": 3, "name": "Bob", "email": "bob@example.com"},
]

status = "PASS" if result == expected else "FAIL"
print(f"\nStatus: {status}")

# Test 2: Reduced fields
print("\n" + "="*70)
print("\nTest 2: Only id and name")
print("-" * 70)
print("Projection: ['id', 'name']")

result = projection.apply(sample_users, ['id', 'name'])
print("\nResult:")
print(json.dumps(result, indent=2))

expected = [
    {"id": 1, "name": "John"},
    {"id": 2, "name": "Jane"},
    {"id": 3, "name": "Bob"},
]

status = "PASS" if result == expected else "FAIL"
print(f"\nStatus: {status}")

# Test 3: Single object projection
print("\n" + "="*70)
print("\nTest 3: Single object projection")
print("-" * 70)
single_user = {"id": 1, "name": "John", "email": "john@example.com", "phone": "111-111-1111"}
print(f"Input: {json.dumps(single_user)}")
print("Projection: ['id', 'email']")

result = projection.apply(single_user, ['id', 'email'])
print(f"\nResult: {json.dumps(result)}")

expected = {"id": 1, "email": "john@example.com"}
status = "PASS" if result == expected else "FAIL"
print(f"Status: {status}")

# Test 4: Nested field projection
print("\n" + "="*70)
print("\nTest 4: Nested field projection (with dict spec)")
print("-" * 70)
nested_projection = {
    "id": True,
    "name": True,
    "address": ["city"]
}
print(f"Projection: {json.dumps(nested_projection)}")

result = projection.apply(sample_users, nested_projection)
print("\nResult:")
print(json.dumps(result, indent=2))

# Test 5: Integration with config
print("\n" + "="*70)
print("\nTest 5: Config Integration")
print("-" * 70)

from nodi.config.loader import ConfigLoader
import tempfile
import os

test_config_yaml = """
services:
  testapi:
    dev:
      base_url: https://api.example.com
    aliases:
      users: /users
default_environment: dev
default_service: testapi

projections:
  user_summary:
    - id
    - name
    - email

  user_contact:
    - name
    - email
    - phone
"""

with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
    f.write(test_config_yaml)
    temp_config_path = f.name

try:
    loader = ConfigLoader()
    config = loader.load(temp_config_path)

    print("Loaded projections:")
    projections = config.list_projections()
    for name, spec in projections.items():
        print(f"  %{name}: {json.dumps(spec)}")

    # Test projection resolution
    user_summary_spec = config.get_projection("user_summary")
    print(f"\nResolving %user_summary: {json.dumps(user_summary_spec)}")

    # Apply the projection
    result = projection.apply(sample_users, user_summary_spec)
    print("\nApplied to sample data:")
    print(json.dumps(result, indent=2))

    expected = [
        {"id": 1, "name": "John", "email": "john@example.com"},
        {"id": 2, "name": "Jane", "email": "jane@example.com"},
        {"id": 3, "name": "Bob", "email": "bob@example.com"},
    ]

    status = "PASS" if result == expected else "FAIL"
    print(f"\nStatus: {status}")

finally:
    os.unlink(temp_config_path)

print("\n" + "="*70)
print("All tests completed!")
print("="*70)
