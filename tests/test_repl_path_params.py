#!/usr/bin/env python3
"""Test path parameter substitution through the REPL flow."""

from nodi.config.loader import ConfigLoader
from nodi.environment.manager import EnvironmentManager
from nodi.providers.rest import RestProvider
from nodi.providers.base import ProviderRequest

# Load config
loader = ConfigLoader()
config = loader.load("c:\\Users\\Motrola\\.nodi\\config.yml")

# Create environment manager
env_manager = EnvironmentManager(config)
env_manager.switch_context("jsonplaceholder", "dev")

# Test the full flow
print("Testing full REPL flow for path parameter substitution:")
print("="*60)

test_inputs = [
    "user:123",
    "user:456?expand=profile",
    "get:user:789",
    "jsonplaceholder.dev@user:999",
]

for input_str in test_inputs:
    print(f"\nInput: {input_str}")
    print("-" * 60)

    try:
        # This is what REPL does
        spec, url = env_manager.resolve_url(input_str)

        print(f"Service:     {spec.service}")
        print(f"Environment: {spec.environment}")
        print(f"Method:      {spec.method}")
        print(f"Endpoint:    {spec.endpoint}")
        print(f"Path params: {spec.path_params}")
        print(f"Query params: {spec.query_params}")
        print(f"Resolved URL: {url}")

        # Verify the path param was substituted
        if spec.path_params and 'id' in spec.path_params:
            param_value = spec.path_params['id']
            if param_value in url:
                print(f"✓ Path parameter '{param_value}' found in URL")
            else:
                print(f"✗ ERROR: Path parameter '{param_value}' NOT found in URL!")

    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()

print("\n" + "="*60)
print("Testing SWAPI endpoint:")
print("="*60)

# Switch to SWAPI service
env_manager.switch_context("swapi", "dev")

test_input = "person:1"
print(f"\nInput: {test_input}")
print("-" * 60)

try:
    spec, url = env_manager.resolve_url(test_input)

    print(f"Service:     {spec.service}")
    print(f"Environment: {spec.environment}")
    print(f"Endpoint:    {spec.endpoint}")
    print(f"Path params: {spec.path_params}")
    print(f"Resolved URL: {url}")
    print(f"Expected URL: https://swapi.dev/api/people/1/")

    if url == "https://swapi.dev/api/people/1/":
        print("✓ URL matches expected!")
    else:
        print("✗ URL does NOT match expected!")

except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
