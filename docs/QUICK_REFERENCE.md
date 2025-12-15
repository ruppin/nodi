# Nodi REPL Quick Reference

## Variable-Based Header Injection

### Three Ways to Use Variables with Headers

#### 1. Config Headers (Global Default)
**config.yml:**
```yaml
headers:
  dev:
    Cookie: ${var:auth_cookie}

variables:
  auth_cookie: "session_id=default"
```
✅ **Use when:** You want a default value for all requests

---

#### 2. Inline Headers (Per-Request Override)
**REPL:**
```bash
nodi> get users -H Cookie:$auth_cookie2
```
✅ **Use when:** Testing different users quickly, one-off requests

---

#### 3. Session Variables (Update Default)
**REPL:**
```bash
nodi> set-variable auth_cookie session_id=user1
```
✅ **Use when:** Switching context for multiple requests

---

## Command Syntax Cheat Sheet

### Variable Management
```bash
variables                          # List all variables
get-variable auth_cookie          # Get specific variable
set-variable auth_cookie value    # Update variable
```

### Inline Headers with Variables
```bash
# Single header with variable
get users -H Cookie:$auth_cookie2

# Multiple headers
get users -H Cookie:$cookie -H Authorization:Bearer_$token

# Variable substitution formats
-H Header:$var              # Short form
-H Header:${var}            # Explicit form
-H Header:prefix_$var       # Compound value
```

### Standard REPL Commands
```bash
# Navigation
use service.env             # Switch context
service myapi              # Switch service
env dev                    # Switch environment

# Requests
get endpoint               # GET request
post endpoint              # POST request
get endpoint | jq filter   # With jq filter

# Headers
headers                    # Show current headers
set-header Name Value      # Set session header
```

---

## Common Workflows

### Quick User Switching
```yaml
# config.yml
variables:
  user1: "session_id=user1_session"
  user2: "session_id=user2_session"
  admin: "session_id=admin_session"
```

```bash
# REPL
nodi> get profile -H Cookie:$user1
nodi> get profile -H Cookie:$user2
nodi> get profile -H Cookie:$admin
```

### Testing Auth Scenarios
```bash
# Valid credentials
nodi> get /api/admin -H Authorization:Bearer_$valid_token
# Returns: 200 OK

# Invalid credentials
nodi> get /api/admin -H Authorization:Bearer_$invalid_token
# Returns: 401 Unauthorized
```

### Multi-User Testing
```bash
# User 1's data
nodi> get orders -H Cookie:$user1_cookie | length
# Output: 5

# User 2's data
nodi> get orders -H Cookie:$user2_cookie | length
# Output: 2
```

---

## Real-World Example

**Scenario:** Test API as different users

### Setup
```yaml
# ~/.nodi/config.yml
services:
  myapi:
    dev:
      base_url: https://api.dev.example.com
    aliases:
      profile: /api/profile
      orders: /api/orders

headers:
  dev:
    Cookie: ${var:default_cookie}

variables:
  default_cookie: "guest_session"
  user1_cookie: "session_id=user1_abc; user_id=1"
  user2_cookie: "session_id=user2_xyz; user_id=2"
  admin_cookie: "session_id=admin_123; role=admin"
```

### Testing Session
```bash
$ nodi repl

# Default (guest)
nodi [myapi.dev]> get profile
{"user": "guest", "authenticated": false}

# User 1
nodi [myapi.dev]> get profile -H Cookie:$user1_cookie
{"user_id": 1, "name": "John", "authenticated": true}

nodi [myapi.dev]> get orders -H Cookie:$user1_cookie
[{"id": "o1", "total": 99.99}, {"id": "o2", "total": 49.99}]

# User 2
nodi [myapi.dev]> get profile -H Cookie:$user2_cookie
{"user_id": 2, "name": "Jane", "authenticated": true}

nodi [myapi.dev]> get orders -H Cookie:$user2_cookie
[{"id": "o3", "total": 149.99}]

# Admin
nodi [myapi.dev]> get orders -H Cookie:$admin_cookie
[{"id": "o1", ...}, {"id": "o2", ...}, {"id": "o3", ...}]

# Verify user1 can't access admin
nodi [myapi.dev]> get /admin/users -H Cookie:$user1_cookie
403 Forbidden
```

---

## Syntax Quick Reference

| Syntax | Example | Description |
|--------|---------|-------------|
| `$var` | `$auth_cookie` | Variable reference (short) |
| `${var}` | `${auth_cookie}` | Variable reference (explicit) |
| `-H Name:$var` | `-H Cookie:$cookie` | Inline header with variable |
| `-H Name:Value` | `-H X-Custom:test` | Inline header literal |
| `${var:name}` | `${var:auth_cookie}` | Config variable reference |
| `\| jq filter` | `\| .user_id` | jq filter |

---

## Tips

✅ **Store test credentials in variables** - Easy to switch between users
✅ **Use inline `-H` for quick tests** - No need to update session
✅ **Use `set-variable` for context switch** - When making multiple requests
✅ **Check variables first** - Run `variables` to see what's available
✅ **Use descriptive names** - `user1_cookie`, not `cookie1`

❌ **Don't commit real credentials** - Use placeholders in config
❌ **Don't overuse session headers** - Use `-H` for one-off tests
❌ **Don't forget to check** - Run `headers` to verify what will be sent

---

## Getting Help

```bash
nodi> help           # Show all commands
nodi> variables      # List all variables
nodi> headers        # Show current headers
```

For full documentation:
- [Inline Headers Guide](inline-headers.md)
- [REPL Variables Examples](repl-variables-examples.md)
- [Variables Documentation](variables.md)
