# Nodi Quick Start Guide

Get started with Nodi in 5 minutes! This guide covers installation, basic usage, and common workflows.

## Table of Contents
- [Installation](#installation)
- [Initial Setup](#initial-setup)
- [Basic Usage](#basic-usage)
- [Quick Reference](#quick-reference)
- [Common Workflows](#common-workflows)

---

## Installation

### Install from Source

```bash
cd nodi
pip install -e .

# Or with all optional dependencies
pip install -e .[full]
```

### Verify Installation

```bash
nodi --version
nodi --help
```

---

## Initial Setup

### 1. Initialize Configuration

```bash
nodi init
```

This creates `~/.nodi/config.yml`.

### 2. Configure Your Services

Edit `~/.nodi/config.yml`:

```yaml
services:
  my-api:
    dev:
      base_url: https://api.dev.mycompany.com
    prod:
      base_url: https://api.prod.mycompany.com
    aliases:
      users: /api/v1/users
      user: /api/v1/users/{id}
      posts: /api/v1/posts
      post: /api/v1/posts/{id}

default_environment: dev
default_service: my-api
```

### 3. Set Environment Variables (Optional)

Create `.env` file:

```bash
DEV_API_KEY=your-dev-key
PROD_API_KEY=your-prod-key
AUTH_TOKEN=your-token
```

Reference in config:

```yaml
headers:
  dev:
    X-API-Key: ${DEV_API_KEY}
    Authorization: Bearer ${AUTH_TOKEN}
```

### 4. Test Configuration

```bash
nodi validate
nodi services
nodi envs
```

---

## Basic Usage

### Interactive Mode (REPL)

Start the REPL:

```bash
$ nodi repl

nodi [my-api.dev]> users
Status: 200 (145ms)

[
  {"id": 1, "name": "Alice"},
  {"id": 2, "name": "Bob"}
]

nodi [my-api.dev]> user:1
Status: 200 (89ms)

{
  "id": 1,
  "name": "Alice",
  "email": "alice@example.com"
}
```

### Command Line Mode

```bash
# Simple request
nodi request my-api.dev@users

# Different format
nodi request my-api.dev@users --format table

# With filtering
nodi request my-api.dev@users --filter 'length'

# Different environment
nodi request my-api.prod@users
```

---

## Quick Reference

### REPL Commands

```bash
# Service/Environment Management
services                    # List all services
envs                        # List environments
use <service>.<env>        # Switch service and environment
service <name>             # Switch to service
env <name>                 # Switch to environment

# HTTP Requests
get <endpoint>             # GET request
post <endpoint> <json>     # POST request
put <endpoint> <json>      # PUT request
patch <endpoint> <json>    # PATCH request
delete <endpoint>          # DELETE request

# Path Parameters
user:123                   # GET /users/123
post:456                   # GET /posts/456

# Query Parameters
users page=2 limit=10      # GET /users?page=2&limit=10
search q=john status=active # GET /search?q=john&status=active

# Filters & Projections
users | @emails            # Apply predefined filter
users | %user_summary      # Apply predefined projection
users | .[*].email         # Direct jq filter
users | length             # Count items

# Headers
headers                    # Show current headers
set-header <name> <value>  # Set session header
unset-header <name>        # Remove session header
get users -H Cookie:$var   # Inline header with variable

# Variables
variables                  # Show all variables
set-variable <name> <val>  # Set variable value
get-variable <name>        # Get variable value

# Scripts
scripts                    # List all .nodi scripts
show <script>              # Show script content
run <script> [params]      # Run script
run --parallel <scripts>   # Run scripts in parallel
run-suite <suite.yml>      # Run test suite

# Output Formats
format <json|yaml|table>   # Set output format

# History
history                    # Show request history
history clear              # Clear history

# Other
clear                      # Clear screen
help                       # Show help
exit, quit                 # Exit REPL
```

### Request Syntax Patterns

| Pattern | Example | Description |
|---------|---------|-------------|
| `alias` | `users` | GET alias endpoint |
| `alias:id` | `user:123` | GET with path parameter |
| `alias params` | `users page=2` | GET with query parameters |
| `alias \| filter` | `users \| length` | Apply filter to response |
| `method alias json` | `post users {...}` | POST with JSON body |
| `alias -H header` | `get users -H Cookie:$var` | Request with custom header |

### Variable Syntax

| Syntax | Example | Description |
|--------|---------|-------------|
| `$var` | `$auth_token` | Variable reference (short) |
| `${var}` | `${auth_token}` | Variable reference (explicit) |
| `${var:name}` | `${var:auth_token}` | Config variable |
| `$var.field` | `$user.email` | Access nested property |
| `-H Name:$var` | `-H Cookie:$cookie` | Inline header with variable |

### Filter Syntax

| Pattern | Example | Description |
|---------|---------|-------------|
| `@name` | `@emails` | Predefined filter |
| `%name` | `%user_summary` | Predefined projection |
| `.field` | `.email` | Extract field |
| `.[*].field` | `.[*].id` | Extract from array |
| `length` | `length` | Count items |
| `.[0]` | `.[0]` | First item |

---

## Common Workflows

### 1. Switch Environments

```bash
nodi [my-api.dev]> env prod
Switched to environment: prod

nodi [my-api.prod]> users
# Now using production API
```

### 2. Test with Different Users

**Config:**
```yaml
variables:
  user1_cookie: "session_id=user1_abc"
  user2_cookie: "session_id=user2_xyz"
  admin_cookie: "session_id=admin_123"
```

**REPL:**
```bash
# Test as User 1
nodi> get profile -H Cookie:$user1_cookie
{"user_id": 1, "name": "John"}

# Test as User 2
nodi> get profile -H Cookie:$user2_cookie
{"user_id": 2, "name": "Jane"}

# Test as Admin
nodi> get /admin/users -H Cookie:$admin_cookie
[...]
```

### 3. Use Path Parameters

```bash
# Config aliases with parameters
aliases:
  user: /api/v1/users/{id}
  user_posts: /api/v1/users/{userId}/posts
  post: /api/v1/posts/{postId}

# REPL usage
nodi> user:123              # GET /api/v1/users/123
nodi> user_posts:123        # GET /api/v1/users/123/posts
nodi> post:456              # GET /api/v1/posts/456
```

### 4. Filter Responses

```bash
# Count items
nodi> users | length
100

# Get specific field
nodi> user:1 | .email
"alice@example.com"

# Extract from array
nodi> users | .[*].email
["alice@example.com", "bob@example.com", ...]

# Use predefined filter
nodi> users | @emails
["alice@example.com", "bob@example.com"]
```

### 5. Create and Run Scripts

**Create script** `test_api.nodi`:
```nodi
# Test API endpoints
echo "Testing users API..."

GET users | @count
$count = $data
assert $count > 0

echo "Found users"
print $count

GET user:1
assert $data.id == 1

echo "All tests passed!"
```

**Run script:**
```bash
nodi> run test_api.nodi
Testing users API...
Found 100 users
All tests passed!
```

### 6. POST/PUT Requests

```bash
# POST request
nodi> post users {"name": "Charlie", "email": "charlie@example.com"}
Status: 201
{"id": 3, "name": "Charlie", "email": "charlie@example.com"}

# PUT request
nodi> put user:3 {"name": "Charles", "email": "charles@example.com"}
Status: 200
{"id": 3, "name": "Charles", "email": "charles@example.com"}

# DELETE request
nodi> delete user:3
Status: 204
```

### 7. Different Output Formats

```bash
# JSON (default)
nodi> users

# Table format
nodi> format table
nodi> users

┌────┬─────────┬──────────────────────┐
│ id │ name    │ email                │
├────┼─────────┼──────────────────────┤
│ 1  │ Alice   │ alice@example.com    │
│ 2  │ Bob     │ bob@example.com      │
└────┴─────────┴──────────────────────┘

# YAML format
nodi> format yaml
nodi> user:1

id: 1
name: Alice
email: alice@example.com
```

### 8. View Request History

```bash
nodi> history

Recent requests:
  1. GET    my-api.dev/api/v1/users (200 OK, 145ms)
  2. GET    my-api.dev/api/v1/users/1 (200 OK, 89ms)
  3. POST   my-api.dev/api/v1/users (201 Created, 234ms)
```

---

## Tips & Tricks

### 💡 Productivity Tips

1. **Use Tab Completion**: REPL supports tab completion for commands, services, and aliases
2. **History Navigation**: Use Up/Down arrows to navigate command history
3. **Quick Exit**: Ctrl+D or type `exit`
4. **Clear Screen**: Type `clear`
5. **Inline Help**: Type `help` in REPL

### ✅ Best Practices

- **Store test credentials in variables** - Easy to switch between users
- **Use inline `-H` for quick tests** - No need to update session
- **Use `set-variable` for context switch** - When making multiple requests
- **Check variables first** - Run `variables` to see what's available
- **Use descriptive names** - `user1_cookie`, not `cookie1`
- **Organize scripts by feature** - Keep related tests together
- **Use predefined filters** - Faster than typing jq expressions

### ❌ Common Mistakes

- Don't commit real credentials - Use placeholders in config
- Don't overuse session headers - Use `-H` for one-off tests
- Don't forget to check - Run `headers` to verify what will be sent
- Don't skip validation - Run `nodi validate` after config changes

---

## Quick Troubleshooting

### Config not found

```bash
nodi init
# Edit ~/.nodi/config.yml
```

### Invalid service/environment

```bash
nodi validate
nodi services
nodi envs
```

### Connection errors

- Check your `.env` file and API keys
- Verify base URLs are correct
- Test endpoint accessibility with curl/browser

### Import errors

```bash
pip install -e .
# Or with all dependencies
pip install -e .[full]
```

### SSL/Certificate errors

```bash
# In config.yml
services:
  my-api:
    dev:
      verify_ssl: false  # For development only
```

---

## Next Steps

- **Read Full Documentation**: [DOCUMENTATION.md](DOCUMENTATION.md) for comprehensive feature guide
- **Extend Nodi**: [DEVELOPMENT.md](DEVELOPMENT.md) for custom providers and scripting
- **View Examples**: Check `examples/` directory for sample configurations

---

## Getting Help

- **In REPL**: Type `help`
- **Command Line**: `nodi --help`
- **Issues**: Report bugs on GitHub issues page
- **Documentation**: See [DOCUMENTATION.md](DOCUMENTATION.md)

---

**Quick Start Complete!** You're ready to use Nodi for API testing and automation.
