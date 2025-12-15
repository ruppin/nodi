# Nodi REPL Quick Start: Using Variables for Different Users

## Overview

Nodi now supports **runtime variables** that can be used to inject different auth cookies and headers for different users during REST API testing.

## 5-Minute Quick Start

### 1. Start the REPL

```bash
$ cd ~/your-project
$ nodi repl
```

### 2. View Current Variables

```bash
nodi [jsonplaceholder.dev]> variables
```

**Output:**
```
Variables:
  auth_cookie                    → ses***lue
  api_token                      → def***ken
```

### 3. Make a Request with Default Cookie

```bash
nodi [jsonplaceholder.dev]> get users
```

### 4. Switch to User 1's Cookie

```bash
nodi [jsonplaceholder.dev]> set-variable auth_cookie session_id=user1_abc123; user_id=user1
```

### 5. Make Request as User 1

```bash
nodi [jsonplaceholder.dev]> get users
```

### 6. Switch to User 2's Cookie

```bash
nodi [jsonplaceholder.dev]> set-variable auth_cookie session_id=user2_xyz789; user_id=user2
```

### 7. Make Request as User 2

```bash
nodi [jsonplaceholder.dev]> get users
```

## Key REPL Commands

| Command | Description |
|---------|-------------|
| `variables` | Show all variables |
| `set-variable <name> <value>` | Update variable value |
| `get-variable <name>` | Get variable value |
| `headers` | Show current headers (with variables resolved) |

## How It Works

1. **Define variables in [config.yml](.nodi/config.yml):**

```yaml
variables:
  auth_cookie: "session_id=default"
  api_token: "default_token"

headers:
  dev:
    Cookie: ${var:auth_cookie}
    Authorization: Bearer ${var:api_token}
```

2. **Variables are resolved at request time** - when you update a variable, all subsequent requests use the new value

3. **No need to restart REPL** - changes take effect immediately

## Real-World Example

```bash
# Start REPL
$ nodi repl

# Check current user
nodi> get /api/profile
# Returns: {"user_id": "default_user"}

# Switch to admin user
nodi> set-variable auth_cookie session_id=admin_session_abc123

# Now you're admin
nodi> get /api/profile
# Returns: {"user_id": "admin", "role": "admin"}

# Try admin-only endpoint
nodi> get /api/admin/users
# Returns: [{"user_id": "user1"}, {"user_id": "user2"}, ...]

# Switch back to regular user
nodi> set-variable auth_cookie session_id=user1_session_xyz789

# Admin endpoint now fails
nodi> get /api/admin/users
# Returns: 403 Forbidden
```

## Next Steps

- Read [REPL Variables Examples](repl-variables-examples.md) for more detailed usage
- Read [Variables Guide](variables.md) for configuration details
- Try it with your own API!

## Tips

✅ **Check which user you are:** Always run `get profile` or similar endpoint to verify your current user context

✅ **View headers before testing:** Use `headers` command to see resolved variable values

✅ **Use descriptive variable names:** Like `user1_session`, `admin_session`, etc.

❌ **Don't commit real credentials:** Use placeholders in config.yml, set real values in REPL

## Configuration Example

Here's your updated [config.yml](.nodi/config.yml):

```yaml
services:
  jsonplaceholder:
    dev:
      base_url: https://jsonplaceholder.typicode.com
    aliases:
      users: /posts
      user: /posts/{id}

headers:
  dev:
    X-Environment: development
    Cookie: ${var:auth_cookie}
  qa:
    X-Environment: qa
    Cookie: ${var:auth_cookie}
  prod:
    X-Environment: production
    Cookie: ${var:auth_cookie}

variables:
  auth_cookie: "session_id=default_value"
  api_token: "default_api_token"
```

Now you can test as different users without restarting or reconfiguring!
