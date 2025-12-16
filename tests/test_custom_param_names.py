#!/usr/bin/env python3
"""Test path parameter with custom parameter names."""

from nodi.config.loader import ConfigLoader
from nodi.config.models import Config, Service, Environment
from nodi.environment.resolver import URLResolver

# Create a custom config with different parameter names
config = Config()
service = Service(
    name="testapi",
    description="Test API",
    environments={
        "dev": Environment(base_url="https://api.example.com")
    },
    aliases={
        "user_by_id": "/users/{id}",                    # Works - uses {id}
        "user_by_userId": "/users/{userId}",            # Won't work - uses {userId}
        "doc_by_docId": "/documents/{documentId}",      # Won't work - uses {documentId}
        "order_by_orderId": "/orders/{orderId}",        # Won't work - uses {orderId}
    }
)
config.services = {"testapi": service}

resolver = URLResolver(config)

print("Testing custom parameter names:")
print("="*60)

test_cases = [
    ("user_by_id:123", "/users/{id}", "Should work - uses {id}"),
    ("user_by_userId:456", "/users/{userId}", "WON'T work - uses {userId}"),
    ("doc_by_docId:789", "/documents/{documentId}", "WON'T work - uses {documentId}"),
    ("order_by_orderId:abc-123", "/orders/{orderId}", "WON'T work - uses {orderId}"),
]

for input_str, alias_path, description in test_cases:
    print(f"\nTest: {description}")
    print(f"Input:      {input_str}")
    print(f"Alias path: {alias_path}")
    print("-" * 60)

    try:
        spec = resolver.parse(input_str, default_service="testapi", default_env="dev")
        url = resolver.resolve(spec)

        print(f"  Path params: {spec.path_params}")
        print(f"  Resolved URL: {url}")

        # Check if parameter was substituted
        if '{' in url:
            print(f"  Status: FAIL - Placeholder '{url[url.index('{'):url.index('}')+1]}' not substituted!")
        else:
            print(f"  Status: PASS - Parameter substituted")

    except Exception as e:
        print(f"  ERROR: {e}")
