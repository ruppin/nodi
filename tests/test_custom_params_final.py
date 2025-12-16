#!/usr/bin/env python3
"""Test path parameter substitution with custom parameter names."""

from nodi.config.loader import ConfigLoader
from nodi.config.models import Config
from nodi.environment.resolver import URLResolver
import yaml

# Create a test config with custom parameter names
test_config_yaml = """
services:
  testapi:
    dev:
      base_url: https://api.example.com
    aliases:
      user_by_id: /users/{id}
      user_by_userId: /users/{userId}
      doc_by_docId: /documents/{documentId}
      order_by_orderId: /orders/{orderId}
      item_by_sku: /items/{itemSku}
default_environment: dev
default_service: testapi
"""

# Write test config to temp file
import tempfile
import os

with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
    f.write(test_config_yaml)
    temp_config_path = f.name

try:
    # Load the test config
    loader = ConfigLoader()
    config = loader.load(temp_config_path)

    # Create resolver
    resolver = URLResolver(config)

    print("Testing custom parameter names:")
    print("="*70)

    test_cases = [
        ("user_by_id:123", "/users/{id}", "https://api.example.com/users/123"),
        ("user_by_userId:456", "/users/{userId}", "https://api.example.com/users/456"),
        ("doc_by_docId:abc-789", "/documents/{documentId}", "https://api.example.com/documents/abc-789"),
        ("order_by_orderId:ord-999", "/orders/{orderId}", "https://api.example.com/orders/ord-999"),
        ("item_by_sku:SKU-2024-001", "/items/{itemSku}", "https://api.example.com/items/SKU-2024-001"),
    ]

    for input_str, alias_template, expected_url in test_cases:
        print(f"\nInput:          {input_str}")
        print(f"Alias template: {alias_template}")
        print("-" * 70)

        try:
            spec = resolver.parse(input_str, default_service="testapi", default_env="dev")
            url = resolver.resolve(spec)

            print(f"  Path params: {spec.path_params}")
            print(f"  Resolved URL: {url}")
            print(f"  Expected URL: {expected_url}")

            if url == expected_url:
                print(f"  Status: PASS")
            else:
                print(f"  Status: FAIL - URLs don't match!")

            if '{' in url:
                print(f"  ERROR: Placeholder not substituted!")

        except Exception as e:
            print(f"  ERROR: {e}")
            import traceback
            traceback.print_exc()

    print("\n" + "="*70)
    print("All tests completed!")

finally:
    # Clean up temp file
    os.unlink(temp_config_path)
