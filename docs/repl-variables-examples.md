# Using Variables in Nodi REPL

This guide shows how to use variables within the Nodi REPL to manage different auth cookies and headers for different users.

## Basic REPL Commands for Variables

### View All Variables

```bash
nodi [jsonplaceholder.dev]> variables
```

**Output:**
```
Variables:
  auth_cookie                    → ses***ue
  api_token                      → def***en
```

### Get a Specific Variable

```bash
nodi [jsonplaceholder.dev]> get-variable auth_cookie
```

**Output:**
```
auth_cookie: ses***lue
```

### Set a Variable

```bash
nodi [jsonplaceholder.dev]> set-variable auth_cookie session_id=user1_session; user_id=user1
```

**Output:**
```
Set variable: auth_cookie
```

## Complete Example: Switching Between Different Users

### Scenario

You have a REST API that requires authentication via cookies, and you want to test requests as different users.

### Step 1: Configure Your config.yml

First, set up your [config.yml](.nodi/config.yml):

```yaml
services:
  myapi:
    dev:
      base_url: https://api.dev.example.com
    aliases:
      profile: /api/v1/profile
      orders: /api/v1/orders
      cart: /api/v1/cart

headers:
  dev:
    X-Environment: development
    Cookie: ${var:auth_cookie}
    Authorization: Bearer ${var:api_token}

variables:
  auth_cookie: "session_id=default"
  api_token: "default_token"
```

### Step 2: Start the REPL

```bash
$ nodi repl
```

### Step 3: View Current Variables

```bash
nodi [myapi.dev]> variables
```

**Output:**
```
Variables:
  auth_cookie                    → ses***ult
  api_token                      → def***ken
```

### Step 4: View Current Headers

```bash
nodi [myapi.dev]> headers
```

**Output:**
```
Headers for myapi.dev:
  User-Agent: nodi/0.1.0
  Accept: application/json, */*
  X-Environment: development
  Cookie: ses***ult
  Authorization: Bea***ken
```

### Step 5: Make a Request as Default User

```bash
nodi [myapi.dev]> get profile
```

**Output:**
```
Status: 200 (145ms)

{
  "user_id": "default_user",
  "name": "Default User",
  "email": "default@example.com"
}
```

### Step 6: Switch to User 1

Update the auth cookie for User 1:

```bash
nodi [myapi.dev]> set-variable auth_cookie session_id=abc123xyz; user_id=user1
```

**Output:**
```
Set variable: auth_cookie
```

### Step 7: Make Request as User 1

```bash
nodi [myapi.dev]> get profile
```

**Output:**
```
Status: 200 (132ms)

{
  "user_id": "user1",
  "name": "John Doe",
  "email": "john@example.com"
}
```

### Step 8: Check User 1's Orders

```bash
nodi [myapi.dev]> get orders
```

**Output:**
```
Status: 200 (156ms)

[
  {
    "order_id": "ord_123",
    "user_id": "user1",
    "total": 99.99,
    "status": "completed"
  },
  {
    "order_id": "ord_456",
    "user_id": "user1",
    "total": 49.99,
    "status": "pending"
  }
]
```

### Step 9: Switch to User 2

```bash
nodi [myapi.dev]> set-variable auth_cookie session_id=xyz789abc; user_id=user2
```

**Output:**
```
Set variable: auth_cookie
```

### Step 10: Check User 2's Profile

```bash
nodi [myapi.dev]> get profile
```

**Output:**
```
Status: 200 (128ms)

{
  "user_id": "user2",
  "name": "Jane Smith",
  "email": "jane@example.com"
}
```

### Step 11: Verify Headers Changed

```bash
nodi [myapi.dev]> headers
```

**Output:**
```
Headers for myapi.dev:
  User-Agent: nodi/0.1.0
  Accept: application/json, */*
  X-Environment: development
  Cookie: xyz***bc
  Authorization: Bea***ken
```

Notice the Cookie value changed!

## Advanced Examples

### Example 1: Testing Different API Tokens

```bash
# Set token for admin user
nodi> set-variable api_token eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.admin_token

# Make admin request
nodi> get /api/admin/users

# Switch to regular user token
nodi> set-variable api_token eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.user_token

# Regular user should get 403
nodi> get /api/admin/users
```

### Example 2: Per-Environment Variables

Your config.yml can have different variable references per environment:

```yaml
variables:
  dev_cookie: "session_id=dev_session"
  qa_cookie: "session_id=qa_session"
  prod_cookie: "session_id=prod_session"

headers:
  dev:
    Cookie: ${var:dev_cookie}
  qa:
    Cookie: ${var:qa_cookie}
  prod:
    Cookie: ${var:prod_cookie}
```

Then in REPL:

```bash
# Switch to QA environment
nodi> use myapi.qa

# Update QA cookie for specific user
nodi> set-variable qa_cookie session_id=qa_user1_session

# Make request
nodi> get profile
```

### Example 3: Multiple Authentication Methods

```yaml
variables:
  cookie_auth: "session_id=default"
  bearer_token: "default_token"
  api_key: "default_key"

headers:
  dev:
    # Use cookie auth by default
    Cookie: ${var:cookie_auth}
    # Comment out token auth
    # Authorization: Bearer ${var:bearer_token}
    # Comment out API key auth
    # X-API-Key: ${var:api_key}
```

Switch between auth methods using session headers:

```bash
# Use cookie auth (default)
nodi> get profile

# Switch to Bearer token auth
nodi> unset-header Cookie
nodi> set-header Authorization Bearer eyJhbGc...

# Switch to API Key auth
nodi> unset-header Authorization
nodi> set-header X-API-Key sk_live_123456789
```

### Example 4: Correlation IDs for Tracing

```yaml
variables:
  correlation_id: "initial-correlation-id"

headers:
  dev:
    X-Correlation-ID: ${var:correlation_id}
    Cookie: ${var:auth_cookie}
```

Update per request for tracing:

```bash
# Generate unique correlation ID for request 1
nodi> set-variable correlation_id req-001-abc123

# Make request
nodi> get /api/users

# Generate new correlation ID for request 2
nodi> set-variable correlation_id req-002-def456

# Make request
nodi> get /api/orders
```

## Session Workflow Example

### Testing User Checkout Flow

```bash
# Start REPL
$ nodi repl

# Set up as User 1
nodi> set-variable auth_cookie session_id=user1_session

# Step 1: View cart
nodi> get cart
# {"items": [], "total": 0}

# Step 2: Add item to cart (POST)
nodi> post cart {"product_id": "prod_123", "quantity": 2}
# {"items": [{"product_id": "prod_123", "quantity": 2}], "total": 39.98}

# Step 3: View updated cart
nodi> get cart
# {"items": [{"product_id": "prod_123", "quantity": 2}], "total": 39.98}

# Step 4: Checkout
nodi> post orders/checkout {"payment_method": "credit_card"}
# {"order_id": "ord_789", "status": "completed", "total": 39.98}

# Step 5: View orders
nodi> get orders
# [{"order_id": "ord_789", "status": "completed", "total": 39.98}]

# Now test as different user
nodi> set-variable auth_cookie session_id=user2_session

# User 2 should have empty cart
nodi> get cart
# {"items": [], "total": 0}
```

## Combining with Filters

Variables work seamlessly with jq filters:

```bash
# Set user
nodi> set-variable auth_cookie session_id=user1_session

# Get orders and filter for pending only
nodi> get orders | .[] | select(.status == "pending")

# Get profile name
nodi> get profile | .name

# Count items in cart
nodi> get cart | .items | length
```

## Tips and Best Practices

### 1. Use Descriptive Variable Names

```yaml
variables:
  user1_session_cookie: "session_id=user1"
  user2_session_cookie: "session_id=user2"
  admin_session_cookie: "session_id=admin"
```

### 2. Store Common User Tokens in Config

Keep frequently-used test user credentials in your config:

```yaml
variables:
  # Test users
  user1_cookie: "session_id=user1_test_session"
  user2_cookie: "session_id=user2_test_session"
  admin_cookie: "session_id=admin_test_session"

  # Active cookie (change this in REPL)
  auth_cookie: "session_id=default"

headers:
  dev:
    Cookie: ${var:auth_cookie}
```

Then switch easily:

```bash
# Switch to user1
nodi> get-variable user1_cookie
nodi> set-variable auth_cookie <paste value>

# Or manually set
nodi> set-variable auth_cookie session_id=user1_test_session
```

### 3. Check Variables Before Making Requests

```bash
# Always verify your context
nodi> variables
nodi> headers
nodi> get profile  # Confirm which user you're acting as
```

### 4. Security Note

**Never commit real auth cookies or tokens to config.yml!** Use placeholder values in the config file and set real values in the REPL session.

```yaml
# Good - placeholder values
variables:
  auth_cookie: "REPLACE_WITH_REAL_COOKIE"
  api_token: "REPLACE_WITH_REAL_TOKEN"
```

```bash
# Then in REPL, set real values
nodi> set-variable auth_cookie <real cookie from browser>
```

## Quick Reference

| Command | Description | Example |
|---------|-------------|---------|
| `variables` | Show all variables | `variables` |
| `get-variable <name>` | Get variable value | `get-variable auth_cookie` |
| `set-variable <name> <value>` | Set variable value | `set-variable auth_cookie session=abc` |
| `headers` | Show current headers (with variables resolved) | `headers` |
| `set-header <name> <value>` | Set session header (bypasses variables) | `set-header Cookie abc=123` |

## Troubleshooting

### Issue: Variable Not Substituted

**Symptom:** Header shows `${var:auth_cookie}` literally

**Solution:** Check variable syntax in config.yml. Must use exact format: `${var:variable_name}`

### Issue: Old Value Still Used

**Symptom:** Updated variable but old value appears in requests

**Solution:** Variables are resolved at request time. Try viewing headers to confirm:
```bash
nodi> set-variable auth_cookie new_value
nodi> headers  # Should show new value
```

### Issue: Variable Not Found

**Symptom:** Warning "Variable not found"

**Solution:** Variable must be defined in config.yml `variables` section first, or set in REPL before use.

## Complete REPL Session Example

Here's a complete session showing variable usage:

```bash
$ cd ~/projects/myapp
$ nodi repl

Nodi - Interactive Data Query Tool
Type 'help' for available commands, 'exit' to quit

Current context: myapi.dev

nodi [myapi.dev]> variables
Variables:
  auth_cookie                    → ses***ult
  api_token                      → def***ken

nodi [myapi.dev]> get profile
Status: 200 (145ms)

{
  "user_id": "default_user",
  "name": "Default User"
}

nodi [myapi.dev]> set-variable auth_cookie session_id=user1_abc123
Set variable: auth_cookie

nodi [myapi.dev]> get profile
Status: 200 (132ms)

{
  "user_id": "user1",
  "name": "John Doe"
}

nodi [myapi.dev]> get orders | length
Status: 200 (156ms)

3

nodi [myapi.dev]> set-variable auth_cookie session_id=user2_xyz789
Set variable: auth_cookie

nodi [myapi.dev]> get profile
Status: 200 (128ms)

{
  "user_id": "user2",
  "name": "Jane Smith"
}

nodi [myapi.dev]> get orders | length
Status: 200 (141ms)

1

nodi [myapi.dev]> exit
Goodbye!
```

This shows switching between users and seeing different results based on the auth cookie variable!
