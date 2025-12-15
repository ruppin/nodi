# Inline Headers with Variable Substitution

## Overview

Nodi REPL now supports **inline header overrides** with automatic variable substitution using the `-H` flag. This allows you to dynamically inject different auth cookies and headers directly in your request commands.

## Syntax

```bash
<method> <endpoint> -H <header_name>:<header_value>
```

### Variable Substitution Formats

You can reference variables using either syntax:
- `$variable_name` - Short form
- `${variable_name}` - Explicit form (same as config.yml)

Both formats work identically in `-H` flags.

## Quick Examples

### Example 1: Override Cookie with Variable

```bash
# auth_cookie2 defined in config.yml variables section
nodi> get users -H Cookie:$auth_cookie2
```

### Example 2: Override Authorization Header

```bash
# bearer_token defined in config.yml
nodi> get profile -H Authorization:Bearer_$bearer_token
```

### Example 3: Multiple Headers

```bash
nodi> get orders -H Cookie:$auth_cookie2 -H X-Correlation-ID:$correlation_id
```

## How It Works

1. **Variables are defined in [config.yml](.nodi/config.yml):**

```yaml
variables:
  auth_cookie: "session_id=default_value"
  auth_cookie2: "session_id=user2_session; user_id=user2"
  bearer_token: "eyJhbGc...token_here"
```

2. **Use `-H` flag in REPL commands:**

```bash
nodi> get users -H Cookie:$auth_cookie2
```

3. **Variable is substituted at request time:**
   - The REPL looks up `auth_cookie2` from the config variables
   - Replaces `$auth_cookie2` with `session_id=user2_session; user_id=user2`
   - Sends the request with the actual cookie value

4. **Header overrides config defaults:**
   - If your config has `Cookie: ${var:auth_cookie}` in headers section
   - Using `-H Cookie:$auth_cookie2` will override it for that request only
   - Next request without `-H` goes back to using the default

## Complete Example Workflow

### Setup config.yml

```yaml
services:
  myapi:
    dev:
      base_url: https://api.dev.example.com
    aliases:
      profile: /api/v1/profile
      orders: /api/v1/orders

headers:
  dev:
    Cookie: ${var:auth_cookie}  # Default cookie

variables:
  # Default user
  auth_cookie: "session_id=default_user"

  # Test users
  auth_cookie_user1: "session_id=user1_abc123; user_id=user1"
  auth_cookie_user2: "session_id=user2_xyz789; user_id=user2"
  auth_cookie_admin: "session_id=admin_session; user_id=admin; role=admin"

  # Tokens
  user1_token: "eyJhbGc...user1_token"
  admin_token: "eyJhbGc...admin_token"
```

### Test Different Users in REPL

```bash
$ nodi repl

# Test as default user (from headers section)
nodi [myapi.dev]> get profile
# Uses: Cookie: session_id=default_user

# Test as User 1 (inline override)
nodi [myapi.dev]> get profile -H Cookie:$auth_cookie_user1
# Uses: Cookie: session_id=user1_abc123; user_id=user1

# Test as User 2 (inline override)
nodi [myapi.dev]> get profile -H Cookie:$auth_cookie_user2
# Uses: Cookie: session_id=user2_xyz789; user_id=user2

# Test as Admin (inline override)
nodi [myapi.dev]> get profile -H Cookie:$auth_cookie_admin
# Uses: Cookie: session_id=admin_session; user_id=admin; role=admin

# Next request goes back to default
nodi [myapi.dev]> get profile
# Uses: Cookie: session_id=default_user
```

## Advanced Use Cases

### 1. Testing Different Auth Methods

```yaml
variables:
  cookie_auth: "session_id=test_session"
  bearer_token: "eyJhbGc..."
  api_key: "sk_live_123456"
```

```bash
# Test with cookie auth
nodi> get /api/users -H Cookie:$cookie_auth

# Test with Bearer token
nodi> get /api/users -H Authorization:Bearer_$bearer_token

# Test with API key
nodi> get /api/users -H X-API-Key:$api_key
```

### 2. Per-Request Correlation IDs

```yaml
variables:
  correlation_id: "corr-123"
```

```bash
# Request 1
nodi> get /api/users -H X-Correlation-ID:req-001

# Request 2 with variable
nodi> get /api/orders -H X-Correlation-ID:$correlation_id
```

### 3. Combining Multiple Overrides

```bash
# Override both cookie and correlation ID
nodi> get orders -H Cookie:$auth_cookie_user2 -H X-Correlation-ID:user2-request-001
```

### 4. Testing Authorization Failures

```yaml
variables:
  invalid_cookie: "session_id=invalid"
  expired_token: "eyJhbGc...expired"
```

```bash
# Test with invalid credentials
nodi> get /api/admin/users -H Cookie:$invalid_cookie
# Expected: 401 Unauthorized

# Test with expired token
nodi> get /api/profile -H Authorization:Bearer_$expired_token
# Expected: 401 Unauthorized
```

## Comparison: Three Ways to Set Headers

### Method 1: Config Headers (Persistent)

**config.yml:**
```yaml
headers:
  dev:
    Cookie: ${var:auth_cookie}
```

**Usage:** Applies to ALL requests automatically

**Best for:** Default values that rarely change

### Method 2: Session Headers (Semi-Persistent)

**REPL:**
```bash
nodi> set-header Cookie session_id=user1_session
```

**Usage:** Applies to all requests in current REPL session

**Best for:** Temporary context switch for multiple requests

### Method 3: Inline Headers (One-Time)

**REPL:**
```bash
nodi> get users -H Cookie:$auth_cookie2
```

**Usage:** Applies to this request only

**Best for:** Quick tests, one-off requests, comparing different users

## Tips and Best Practices

### ✅ DO

1. **Define test user credentials in config variables:**
   ```yaml
   variables:
     user1_cookie: "session_id=user1_test"
     user2_cookie: "session_id=user2_test"
   ```

2. **Use descriptive variable names:**
   - Good: `auth_cookie_admin`, `bearer_token_user1`
   - Bad: `cookie1`, `token2`

3. **Test both valid and invalid credentials:**
   ```bash
   nodi> get profile -H Cookie:$valid_cookie
   nodi> get profile -H Cookie:$invalid_cookie
   ```

4. **Combine with jq filters for quick validation:**
   ```bash
   nodi> get profile -H Cookie:$auth_cookie_user1 | .user_id
   # Should output: "user1"
   ```

### ❌ DON'T

1. **Don't commit real credentials to config.yml:**
   ```yaml
   # BAD - real credentials in version control
   variables:
     prod_cookie: "session_id=real_production_cookie"

   # GOOD - placeholder values
   variables:
     prod_cookie: "REPLACE_WITH_REAL_COOKIE"
   ```

2. **Don't use inline headers for permanent changes:**
   ```bash
   # If you need this header for many requests, use set-header instead
   nodi> set-header Cookie $auth_cookie2
   ```

## Syntax Reference

### Header Format Options

```bash
# Colon with no space
-H Cookie:$auth_cookie

# Colon with space (both parts trimmed)
-H "Cookie: $auth_cookie"

# Multiple headers
-H Cookie:$cookie -H Authorization:Bearer_$token

# Literal values (no variable)
-H X-Custom-Header:literal_value
```

### Variable Reference Formats

```bash
# Short form (recommended for simple names)
-H Cookie:$auth_cookie

# Explicit form (same as config.yml)
-H Cookie:${auth_cookie}

# In compound values
-H Authorization:Bearer_$token
-H Cookie:session=$session_id;_user=$user_id

# If variable not found, literal value used
-H Cookie:$nonexistent_var
# Sends: Cookie: $nonexistent_var
```

## Complete Real-World Example

### Scenario: E-commerce API Testing

**config.yml:**
```yaml
services:
  shop-api:
    dev:
      base_url: https://shop.dev.example.com
    aliases:
      cart: /api/v1/cart
      checkout: /api/v1/checkout
      orders: /api/v1/orders
      profile: /api/v1/profile

headers:
  dev:
    X-Environment: development
    Cookie: ${var:default_cookie}

variables:
  # Test users
  default_cookie: "session_id=guest"
  customer1_cookie: "session_id=cust1_abc; user_id=customer1"
  customer2_cookie: "session_id=cust2_xyz; user_id=customer2"
  admin_cookie: "session_id=admin_123; user_id=admin; role=admin"
```

**REPL Session:**
```bash
$ nodi repl

# Test guest user (default)
nodi [shop-api.dev]> get cart
# Response: {"items": [], "total": 0, "user": "guest"}

# Test customer1's cart
nodi [shop-api.dev]> get cart -H Cookie:$customer1_cookie
# Response: {"items": [...], "total": 99.99, "user": "customer1"}

# Test customer2's cart
nodi [shop-api.dev]> get cart -H Cookie:$customer2_cookie
# Response: {"items": [...], "total": 149.99, "user": "customer2"}

# Admin view all orders
nodi [shop-api.dev]> get orders -H Cookie:$admin_cookie
# Response: [{"order_id": "1", "customer": "customer1"}, ...]

# Customer1 tries to access admin endpoint (should fail)
nodi [shop-api.dev]> get orders -H Cookie:$customer1_cookie
# Response: 403 Forbidden

# Customer1 places order
nodi [shop-api.dev]> post checkout -H Cookie:$customer1_cookie
# Response: {"order_id": "ord_123", "status": "success"}

# Verify order created
nodi [shop-api.dev]> get orders -H Cookie:$customer1_cookie | .[] | .order_id
# Response: "ord_123"
```

## Troubleshooting

### Issue: Variable not substituted

**Symptom:** Header contains literal `$variable_name`

**Cause:** Variable not defined in config.yml

**Solution:**
```bash
# Check available variables
nodi> variables

# Add to config.yml if missing
variables:
  variable_name: "value"
```

### Issue: Header not overriding

**Symptom:** Request still uses default header

**Cause:** Wrong header name or syntax error

**Solution:**
```bash
# Check current headers
nodi> headers

# Verify -H syntax (colon required)
nodi> get users -H Cookie:$auth_cookie2  # Correct
nodi> get users -H Cookie $auth_cookie2   # Wrong - no colon
```

### Issue: Special characters in value

**Symptom:** Cookie value truncated or malformed

**Cause:** Shell parsing issues

**Solution:** Store complex values in variables
```yaml
# In config.yml
variables:
  complex_cookie: "session_id=abc123; user=john@example.com; flags=a,b,c"
```

```bash
# In REPL
nodi> get users -H Cookie:$complex_cookie
```

## Summary

**Inline header syntax with variables provides the most flexible way to test APIs with different users:**

| Feature | Syntax | Use Case |
|---------|--------|----------|
| Simple override | `-H Cookie:$var` | Quick user switching |
| Multiple headers | `-H Cookie:$c -H Auth:$a` | Override multiple values |
| Literal values | `-H X-Custom:value` | One-off custom headers |
| Variable substitution | `$var` or `${var}` | Reference config variables |

This makes testing multi-user scenarios fast and intuitive! 🚀
