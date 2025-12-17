# Python Scripting in Nodi

Complete guide to using full Python scripts in Nodi for advanced API testing and automation.

## Overview

Nodi supports **two types of scripts**:

1. **.nodi files** - Simple DSL for quick API testing (see [SCRIPTING.md](SCRIPTING.md))
2. **.py files** - Full Python scripts for complex workflows (this document)

### When to Use Python Scripts

Use Python scripts (`.py`) when you need:
- Complex data processing or transformations
- Python libraries and modules
- Advanced control flow (try/catch, while loops, etc.)
- Object-oriented programming
- Integration with existing Python code
- Custom algorithms or calculations

Use `.nodi` DSL when you need:
- Quick, simple API tests
- Minimal syntax for common tasks
- Sandboxed, safe execution
- Learning-friendly scripts

---

## Quick Start

### 1. Your First Python Script

Create `test_api.py`:

```python
"""My first Nodi Python script."""

# The 'nodi' object and 'client' are automatically available
print("Testing API...")

# Make a GET request
response = client.get("users")

# Check response
response.assert_ok()

# Get JSON data
users = response.json()

print(f"Found {len(users)} users")

# Python assertions
assert len(users) > 0, "Expected at least one user"

print("✓ Test passed!")
```

### 2. Run the Script

```bash
# In REPL
nodi> run test_api.py

# Or from command line
nodi run test_api.py
```

---

## Nodi Python API

### Injected Objects

Every Python script has these objects automatically available:

```python
nodi      # Main Nodi API object
client    # HTTP client for making requests
```

### HTTP Client (`client`)

#### Making Requests

```python
# GET request
response = client.get("users")
response = client.get("users", params={'page': 1, 'limit': 10})

# POST request
response = client.post("users", json={
    "name": "John Doe",
    "email": "john@example.com"
})

# PUT request
response = client.put("user:123", json={
    "name": "Updated Name"
})

# PATCH request
response = client.patch("user:123", json={
    "email": "new@example.com"
})

# DELETE request
response = client.delete("user:123")

# Other methods
response = client.head("users")
response = client.options("users")
```

#### Request Options

```python
# With headers
response = client.get("users", headers={
    "X-Custom-Header": "value"
})

# With query parameters
response = client.get("users", params={
    "page": 2,
    "limit": 20,
    "sort": "name"
})

# With timeout
response = client.get("users", timeout=60)

# POST with different data formats
response = client.post("users", json={"name": "John"})  # JSON
response = client.post("users", data="raw string data")  # Raw data
```

#### Session Headers

```python
# Set header for all requests in session
client.set_header("Authorization", "Bearer token123")

# Remove session header
client.unset_header("Authorization")

# Get current session headers
headers = client.get_headers()
```

### Response Object

```python
response = client.get("users")

# Status code
status = response.status_code  # 200, 404, etc.

# Check if successful
if response.ok:  # True for 2xx status
    print("Success!")

if response.is_error:  # True for 4xx, 5xx
    print("Error!")

# Get data
data = response.json()  # Parse as JSON
text = response.text()   # Get as text string

# Headers
content_type = response.headers['Content-Type']

# Response time
elapsed = response.elapsed_ms  # Time in milliseconds

# Assertions
response.assert_status(200)  # Assert specific status
response.assert_ok()         # Assert 2xx status
response.assert_status(201, "Expected resource created")  # With message
```

### Nodi API (`nodi`)

```python
# Access configuration
config = nodi.config

# Variables
user_id = nodi.get_variable('user_id', default=1)
nodi.set_variable('user_id', 123)
all_vars = nodi.vars  # Dictionary of all variables

# Apply filters
emails = nodi.apply_filter(users, '.[*].email')

# Apply projections
summary = nodi.apply_projection(users, 'user_summary')

# Get predefined filter
filter_expr = nodi.get_filter('active_users')

# Logging
nodi.echo("This is a message")
nodi.log("Important info", level='INFO')
nodi.log("Warning message", level='WARNING')
nodi.log("Error occurred", level='ERROR')
```

---

## Advanced Features

### 1. Using Python Libraries

You can import and use Python's standard library:

```python
import json
import datetime
from collections import Counter

# Get users
response = client.get("users")
users = response.json()

# Use Counter for analysis
emails = [u['email'] for u in users]
domains = [e.split('@')[1] for e in emails if '@' in e]
domain_counts = Counter(domains)

print(f"Top domains: {domain_counts.most_common(3)}")

# Save to JSON file
with open('users_export.json', 'w') as f:
    json.dump(users, f, indent=2)

print(f"Exported at {datetime.datetime.now()}")
```

**Allowed modules** (safe list):
- json, datetime, time, math, random
- collections, itertools, functools, re
- string, decimal, statistics, base64
- hashlib, hmac, uuid, enum, csv
- typing, dataclasses

**Restricted modules** (for security):
- os, subprocess, sys
- eval, exec, __import__
- file operations (except in scripts)

### 2. Object-Oriented Programming

```python
class UserTester:
    """Test user endpoints."""

    def __init__(self, client):
        self.client = client
        self.test_results = []

    def test_get_users(self):
        """Test GET /users."""
        response = self.client.get("users")
        response.assert_ok()

        users = response.json()
        assert len(users) > 0

        self.test_results.append(('get_users', 'PASS'))
        return users

    def test_get_user(self, user_id):
        """Test GET /users/:id."""
        response = self.client.get(f"user:{user_id}")
        response.assert_ok()

        user = response.json()
        assert user['id'] == user_id

        self.test_results.append(('get_user', 'PASS'))
        return user

    def report(self):
        """Generate test report."""
        total = len(self.test_results)
        passed = sum(1 for _, status in self.test_results if status == 'PASS')

        print(f"\nTest Results: {passed}/{total} passed")
        for test_name, status in self.test_results:
            print(f"  {test_name}: {status}")

# Use the class
tester = UserTester(client)
users = tester.test_get_users()
tester.test_get_user(users[0]['id'])
tester.report()
```

### 3. Complex Data Processing

```python
# Get posts and users
posts_response = client.get("posts")
users_response = client.get("users")

posts = posts_response.json()
users = users_response.json()

# Create user lookup dictionary
users_by_id = {u['id']: u for u in users}

# Enrich posts with user data
enriched_posts = []
for post in posts:
    user = users_by_id.get(post['userId'])
    if user:
        enriched_posts.append({
            'post_id': post['id'],
            'title': post['title'],
            'author_name': user['name'],
            'author_email': user['email']
        })

# Filter and sort
long_titles = [p for p in enriched_posts if len(p['title']) > 50]
sorted_posts = sorted(enriched_posts, key=lambda p: p['author_name'])

print(f"Posts with long titles: {len(long_titles)}")
print(f"Total enriched posts: {len(enriched_posts)}")
```

### 4. Error Handling

```python
def safe_get_user(user_id):
    """Get user with error handling."""
    try:
        response = client.get(f"user:{user_id}")

        if response.status_code == 404:
            print(f"User {user_id} not found")
            return None
        elif response.status_code == 403:
            print(f"Access denied for user {user_id}")
            return None

        response.assert_ok()
        return response.json()

    except AssertionError as e:
        print(f"Assertion failed: {e}")
        return None
    except Exception as e:
        print(f"Error getting user: {e}")
        return None

# Use it
user = safe_get_user(999999)
if user:
    print(f"User: {user['name']}")
else:
    print("Could not get user")
```

### 5. Parameterized Scripts

```python
"""Parameterized test script.

Run with: run test_user.py user_id=5 check_posts=true
"""

# Get parameters (with defaults)
user_id = nodi.get_variable('user_id', default=1)
check_posts = nodi.get_variable('check_posts', default='false')

print(f"Testing user {user_id}")

# Get user
response = client.get(f"user:{user_id}")
response.assert_ok()

user = response.json()
print(f"User: {user['name']}")

# Conditional logic based on parameter
if check_posts.lower() == 'true':
    posts_response = client.get("posts", params={'userId': user_id})
    posts = posts_response.json()
    print(f"User has {len(posts)} posts")
```

Run it:
```bash
nodi> run test_user.py user_id=5 check_posts=true
```

---

## Best Practices

### 1. Script Structure

```python
"""Script description.

This script tests the user API endpoints.
"""

# Imports
import json
from datetime import datetime

# Configuration
TEST_USER_ID = 1
TIMEOUT = 30

# Helper functions
def validate_user(user):
    """Validate user object structure."""
    required_fields = ['id', 'name', 'email']
    for field in required_fields:
        assert field in user, f"Missing field: {field}"

# Main test functions
def test_get_users():
    """Test GET /users."""
    response = client.get("users", timeout=TIMEOUT)
    response.assert_ok()
    return response.json()

def test_get_user_details():
    """Test GET /users/:id."""
    response = client.get(f"user:{TEST_USER_ID}")
    response.assert_ok()

    user = response.json()
    validate_user(user)
    return user

# Main execution
if __name__ == "__main__":
    print("=" * 70)
    print(f"User API Tests - {datetime.now()}")
    print("=" * 70)

    try:
        users = test_get_users()
        print(f"✓ Found {len(users)} users")

        user = test_get_user_details()
        print(f"✓ User details: {user['name']}")

        print("\n✓ All tests passed!")

    except AssertionError as e:
        print(f"\n✗ Assertion failed: {e}")
        raise
    except Exception as e:
        print(f"\n✗ Error: {e}")
        raise
```

### 2. Reusable Functions

Create a library file `api_helpers.py`:

```python
"""Reusable API testing helpers."""

def get_all_pages(client, endpoint, params=None):
    """Get all pages of paginated data."""
    all_data = []
    page = 1

    while True:
        response = client.get(endpoint, params={'page': page, **(params or {})})

        if not response.ok:
            break

        data = response.json()
        if not data:
            break

        all_data.extend(data)
        page += 1

        # Safety limit
        if page > 100:
            break

    return all_data


def retry_request(client, method, endpoint, max_retries=3, **kwargs):
    """Retry request on failure."""
    import time

    for attempt in range(max_retries):
        try:
            response = getattr(client, method)(endpoint, **kwargs)
            response.assert_ok()
            return response
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            print(f"Retry {attempt + 1}/{max_retries}...")
            time.sleep(2 ** attempt)  # Exponential backoff
```

Use in your script:
```python
# Import will work if api_helpers.py is in the same directory or ~/.nodi/scripts/
from api_helpers import get_all_pages, retry_request

# Get all users across all pages
all_users = get_all_pages(client, "users")

# Retry on failure
response = retry_request(client, 'get', 'unstable-endpoint')
```

### 3. Testing Patterns

```python
def run_test(name, test_func):
    """Run a single test with error handling."""
    try:
        print(f"\n{name}...", end=" ")
        test_func()
        print("✓ PASS")
        return True
    except AssertionError as e:
        print(f"✗ FAIL: {e}")
        return False
    except Exception as e:
        print(f"✗ ERROR: {e}")
        return False


# Define tests
def test_user_list():
    response = client.get("users")
    response.assert_ok()
    assert len(response.json()) > 0

def test_user_details():
    response = client.get("user:1")
    response.assert_ok()
    assert response.json()['id'] == 1

# Run all tests
tests = [
    ("User List", test_user_list),
    ("User Details", test_user_details),
]

results = [run_test(name, func) for name, func in tests]

# Summary
passed = sum(results)
total = len(results)
print(f"\n{'='*50}")
print(f"Results: {passed}/{total} passed")
```

---

## Plugin System

### Creating Plugins

Create `~/.nodi/plugins/my_plugin.py`:

```python
from nodi.plugins import Plugin

class MyCustomPlugin(Plugin):
    """My custom plugin."""

    @property
    def name(self) -> str:
        return "my_plugin"

    @property
    def description(self) -> str:
        return "Does something cool"

    def before_request(self, request):
        """Modify request before sending."""
        # Add custom header
        request.headers['X-Custom'] = 'value'
        return request

    def after_response(self, response):
        """Process response."""
        # Log or transform response
        print(f"Response: {response.status_code}")
        return response
```

### Loading Plugins

In `config.yml`:

```yaml
plugins:
  - my_plugin.MyCustomPlugin
  - name: my_plugin.MyCustomPlugin
    config:
      enabled: true
      custom_setting: value
```

---

## Examples

### Example 1: Data Export

```python
"""Export user data to CSV."""

import csv
import datetime

# Get users
response = client.get("users")
response.assert_ok()
users = response.json()

# Export to CSV
filename = f"users_{datetime.date.today()}.csv"

with open(filename, 'w', newline='') as f:
    if users:
        writer = csv.DictWriter(f, fieldnames=users[0].keys())
        writer.writeheader()
        writer.writerows(users)

print(f"✓ Exported {len(users)} users to {filename}")
```

### Example 2: Performance Testing

```python
"""Performance test - measure response times."""

import time
import statistics

def measure_endpoint(endpoint, iterations=10):
    """Measure endpoint response time."""
    times = []

    for i in range(iterations):
        start = time.time()
        response = client.get(endpoint)
        elapsed = (time.time() - start) * 1000  # ms

        times.append(elapsed)

        if not response.ok:
            print(f"  Request {i+1} failed: {response.status_code}")

    return times

# Test endpoints
endpoints = ["users", "posts", "comments"]

print("Performance Test Results:")
print("=" * 50)

for endpoint in endpoints:
    times = measure_endpoint(endpoint)

    print(f"\n{endpoint}:")
    print(f"  Avg: {statistics.mean(times):.2f}ms")
    print(f"  Min: {min(times):.2f}ms")
    print(f"  Max: {max(times):.2f}ms")
    print(f"  Median: {statistics.median(times):.2f}ms")
```

### Example 3: Data Validation

```python
"""Validate API data against schema."""

def validate_user_schema(user):
    """Validate user object structure."""
    schema = {
        'id': int,
        'name': str,
        'email': str,
        'username': str,
        'phone': str,
        'website': str
    }

    for field, field_type in schema.items():
        assert field in user, f"Missing field: {field}"
        assert isinstance(user[field], field_type), \
            f"Invalid type for {field}: expected {field_type}, got {type(user[field])}"

# Get and validate users
response = client.get("users")
response.assert_ok()

users = response.json()
errors = []

for user in users:
    try:
        validate_user_schema(user)
    except AssertionError as e:
        errors.append(f"User {user.get('id')}: {e}")

if errors:
    print("Validation errors:")
    for error in errors:
        print(f"  - {error}")
else:
    print(f"✓ All {len(users)} users validated successfully")
```

---

## Troubleshooting

### Import Errors

**Problem**: `ModuleNotFoundError: No module named 'requests'`

**Solution**: Only standard library modules are available by default. Use the injected `client` instead.

```python
# DON'T
import requests
response = requests.get("https://api.example.com")

# DO
response = client.get("users")
```

### Timeout Errors

**Problem**: Script times out

**Solution**: Adjust timeout in config or when creating runner:

```yaml
# config.yml
scripting:
  python_timeout: 600  # 10 minutes
```

### Variable Access

**Problem**: `NameError: name 'user_id' is not defined`

**Solution**: Use `nodi.get_variable()` instead of direct access:

```python
# DON'T
user_id = user_id  # May not exist

# DO
user_id = nodi.get_variable('user_id', default=1)
```

---

## Comparison: `.nodi` DSL vs `.py` Python

| Feature | `.nodi` DSL | `.py` Python |
|---------|-------------|--------------|
| **Syntax** | Simple, custom | Full Python |
| **Learning curve** | Easy | Moderate |
| **Power** | Basic | Full Python |
| **Control flow** | Limited (coming) | Full (if/for/while/try) |
| **Libraries** | None | Standard library |
| **Safety** | Sandboxed | Configurable |
| **Best for** | Quick tests | Complex automation |
| **Execution speed** | Fast | Fast |
| **Debugging** | Basic | Full stack traces |

**Recommendation**: Start with `.nodi` for simple tests, use `.py` when you need more power.

---

## See Also

- [Scripting Guide](SCRIPTING.md) - `.nodi` DSL scripting
- [Plugin Development](PLUGINS.md) - Creating plugins
- [API Reference](API_REFERENCE.md) - Complete API docs
- [Examples](../examples/) - More example scripts

---

**Happy Python scripting with Nodi!** 🐍🚀
