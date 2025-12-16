#!/usr/bin/env python3
"""Test path parameter substitution with custom parameter names."""

# Simple test to show the limitation
from nodi.environment.resolver import URLResolver

# Mock path substitution
def test_substitute(path, params):
    """Simulate current implementation."""
    for param_name, param_value in params.items():
        path = path.replace(f"{{{param_name}}}", str(param_value))
    return path

print("Current Implementation Test:")
print("="*60)

# Current implementation - always uses 'id'
current_params = {"id": "123"}

test_cases = [
    ("/users/{id}", "PASS - Parameter name matches"),
    ("/users/{userId}", "FAIL - Parameter name mismatch"),
    ("/documents/{documentId}", "FAIL - Parameter name mismatch"),
    ("/orders/{orderId}", "FAIL - Parameter name mismatch"),
]

print("\nCurrent params:", current_params)
print()

for path_template, description in test_cases:
    result = test_substitute(path_template, current_params)
    status = "FAIL" if '{' in result else "PASS"
    print(f"{description}")
    print(f"  Template: {path_template}")
    print(f"  Result:   {result}")
    print(f"  Status:   {status}")
    print()
