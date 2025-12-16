#!/usr/bin/env python3
"""Test advanced path parameter substitution scenarios."""

from nodi.config.loader import ConfigLoader
from nodi.environment.resolver import URLResolver

# Load config
loader = ConfigLoader()
config = loader.load("c:\\Users\\Motrola\\.nodi\\config.yml")

# Create resolver
resolver = URLResolver(config)

print("Testing advanced path parameter scenarios:\n")
print("="*60)

# Test 1: Simple path param
print("\nTest 1: Simple path parameter")
print("-" * 60)
spec = resolver.parse("user:123", default_service="jsonplaceholder", default_env="dev")
url = resolver.resolve(spec)
print(f"Input:    user:123")
print(f"Endpoint: {spec.endpoint}")
print(f"Params:   {spec.path_params}")
print(f"URL:      {url}")
print(f"Expected: https://jsonplaceholder.typicode.com/posts/123")
print(f"Match:    {url == 'https://jsonplaceholder.typicode.com/posts/123'}")

# Test 2: Path param with query params
print("\nTest 2: Path parameter with query params")
print("-" * 60)
spec = resolver.parse("user:123?expand=true&format=json", default_service="jsonplaceholder", default_env="dev")
url = resolver.resolve(spec)
print(f"Input:    user:123?expand=true&format=json")
print(f"Endpoint: {spec.endpoint}")
print(f"Params:   {spec.path_params}")
print(f"Query:    {spec.query_params}")
print(f"URL:      {url}")
print(f"Expected: https://jsonplaceholder.typicode.com/posts/123?expand=true&format=json")
print(f"Match:    {url == 'https://jsonplaceholder.typicode.com/posts/123?expand=true&format=json'}")

# Test 3: Path param with method
print("\nTest 3: Path parameter with method")
print("-" * 60)
spec = resolver.parse("put:user:123", default_service="jsonplaceholder", default_env="dev")
url = resolver.resolve(spec)
print(f"Input:    put:user:123")
print(f"Method:   {spec.method}")
print(f"Endpoint: {spec.endpoint}")
print(f"Params:   {spec.path_params}")
print(f"URL:      {url}")
print(f"Expected: https://jsonplaceholder.typicode.com/posts/123")
print(f"Match:    {url == 'https://jsonplaceholder.typicode.com/posts/123'}")

# Test 4: Full syntax
print("\nTest 4: Full syntax with service.env")
print("-" * 60)
spec = resolver.parse("jsonplaceholder.dev@user:789", default_service="jsonplaceholder", default_env="dev")
url = resolver.resolve(spec)
print(f"Input:    jsonplaceholder.dev@user:789")
print(f"Service:  {spec.service}")
print(f"Env:      {spec.environment}")
print(f"Endpoint: {spec.endpoint}")
print(f"Params:   {spec.path_params}")
print(f"URL:      {url}")
print(f"Expected: https://jsonplaceholder.typicode.com/posts/789")
print(f"Match:    {url == 'https://jsonplaceholder.typicode.com/posts/789'}")

# Test 5: Direct path (no alias)
print("\nTest 5: Direct path without alias")
print("-" * 60)
spec = resolver.parse("/api/users/456", default_service="jsonplaceholder", default_env="dev")
url = resolver.resolve(spec)
print(f"Input:    /api/users/456")
print(f"Endpoint: {spec.endpoint}")
print(f"Params:   {spec.path_params}")
print(f"URL:      {url}")
print(f"Expected: https://jsonplaceholder.typicode.com/api/users/456")
print(f"Match:    {url == 'https://jsonplaceholder.typicode.com/api/users/456'}")

print("\n" + "="*60)
print("All tests completed!")
