#!/usr/bin/env python3
"""Improved resolver that auto-detects parameter names from alias path."""

import re
from typing import Dict, Optional, Tuple

def extract_path_params_improved(endpoint: str, alias_path: str) -> Tuple[str, Optional[Dict[str, str]]]:
    """
    Extract path parameters from endpoint and match with alias template.

    Examples:
        endpoint="user:123", alias="/users/{id}" -> ("user", {"id": "123"})
        endpoint="user:123", alias="/users/{userId}" -> ("user", {"userId": "123"})
        endpoint="doc:abc-123", alias="/documents/{documentId}" -> ("doc", {"documentId": "abc-123"})
    """
    # Pattern: alias:value or alias:value:rest
    parts = endpoint.split(":")

    if len(parts) == 1:
        # No path params
        return endpoint, None

    # Extract parameter value from endpoint
    alias = parts[0]
    param_value = parts[1]

    # If there are more parts, reconstruct the rest
    if len(parts) > 2:
        rest = ":".join(parts[2:])
        alias = f"{alias}:{rest}"

    # Auto-detect parameter name from alias path
    # Find first {param_name} in the alias path
    param_pattern = re.compile(r'\{(\w+)\}')
    match = param_pattern.search(alias_path)

    if match:
        param_name = match.group(1)  # Extract parameter name (e.g., "userId", "documentId")
        return alias, {param_name: param_value}
    else:
        # No parameter placeholder found, default to 'id'
        return alias, {"id": param_value}


def substitute_path_params_improved(path: str, params: Dict[str, str]) -> str:
    """Substitute path parameters in URL template."""
    # Replace {param} with values
    for param_name, param_value in params.items():
        path = path.replace(f"{{{param_name}}}", str(param_value))

    return path


# Test the improved implementation
print("Improved Implementation Test:")
print("="*60)

test_cases = [
    ("user:123", "/users/{id}", {"id": "123"}),
    ("user:456", "/users/{userId}", {"userId": "456"}),
    ("doc:abc-123", "/documents/{documentId}", {"documentId": "abc-123"}),
    ("order:ord-999", "/orders/{orderId}", {"orderId": "ord-999"}),
    ("item:SKU-2024", "/items/{itemSku}", {"itemSku": "SKU-2024"}),
]

print("\nTesting improved parameter extraction:\n")

for endpoint, alias_path, expected_params in test_cases:
    alias, params = extract_path_params_improved(endpoint, alias_path)
    result = substitute_path_params_improved(alias_path, params)

    status = "PASS" if params == expected_params and '{' not in result else "FAIL"

    print(f"Endpoint:       {endpoint}")
    print(f"Alias path:     {alias_path}")
    print(f"Extracted params: {params}")
    print(f"Expected params:  {expected_params}")
    print(f"Result:         {result}")
    print(f"Status:         {status}")
    print()
