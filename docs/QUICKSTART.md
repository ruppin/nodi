# Nodi Quick Start Guide

This guide will help you get started with Nodi in 5 minutes.

## Installation

```bash
cd nodi
pip install -e .
```

## Initial Setup

### 1. Initialize Configuration

```bash
nodi init
```

This creates `~/.nodi/config.yml`.

### 2. Edit Configuration

Open `~/.nodi/config.yml` and add your services:

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

default_environment: dev
default_service: my-api
```

### 3. Set Environment Variables (Optional)

Create `.env` file in your project:

```bash
DEV_API_KEY=your-dev-key
PROD_API_KEY=your-prod-key
```

Update config to use them:

```yaml
headers:
  dev:
    X-API-Key: ${DEV_API_KEY}
  prod:
    X-API-Key: ${PROD_API_KEY}
```

## Using Nodi

### Interactive Mode (REPL)

```bash
$ nodi

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

## Common Tasks

### List Services

```bash
nodi services
```

### List Environments

```bash
nodi envs
```

### Validate Configuration

```bash
nodi validate
```

### Switch Environment in REPL

```bash
nodi [my-api.dev]> env prod
Switched to environment: prod

nodi [my-api.prod]> users
...
```

### Add Custom Header

```bash
# In REPL
nodi [my-api.dev]> set-header X-Custom-ID abc123

# In CLI
nodi request my-api.dev@users -H "X-Custom-ID: abc123"
```

### View Request History

```bash
nodi [my-api.dev]> history

Recent requests:
  1. ✓ GET    my-api.dev/api/v1/users (200 OK, 145ms)
  2. ✓ GET    my-api.dev/api/v1/users/1 (200 OK, 89ms)
  3. ✓ GET    my-api.prod/api/v1/users (200 OK, 312ms)
```

## Advanced Usage

### Using Aliases with Parameters

Config:
```yaml
aliases:
  user: /api/v1/users/{id}
  profile: /api/v1/users/{id}/profile
```

Usage:
```bash
nodi [my-api.dev]> user:123        # GET /api/v1/users/123
nodi [my-api.dev]> profile:123     # GET /api/v1/users/123/profile
```

### Query Parameters

```bash
nodi [my-api.dev]> users?page=2&limit=10
```

### jq Filtering

```bash
# Count items
nodi [my-api.dev]> users | jq length

# Get specific field
nodi [my-api.dev]> user:1 | jq .email

# Filter array
nodi [my-api.dev]> users | jq '.[] | select(.active == true)'
```

### POST/PUT Requests

```bash
# In REPL
nodi [my-api.dev]> post users {"name": "Charlie", "email": "charlie@example.com"}

# In CLI
nodi request my-api.dev@users --method POST --data '{"name": "Charlie"}'
```

### Different Output Formats

```bash
# Table
nodi [my-api.dev]> format table
nodi [my-api.dev]> users

┌────┬─────────┬──────────────────────┐
│ id │ name    │ email                │
├────┼─────────┼──────────────────────┤
│ 1  │ Alice   │ alice@example.com    │
│ 2  │ Bob     │ bob@example.com      │
└────┴─────────┴──────────────────────┘

# YAML
nodi [my-api.dev]> format yaml
nodi [my-api.dev]> user:1

id: 1
name: Alice
email: alice@example.com
```

## Tips

1. **Use Tab Completion**: The REPL supports tab completion for commands, services, and aliases
2. **History Navigation**: Use Up/Down arrows to navigate command history
3. **Quick Exit**: Ctrl+D or type `exit`
4. **Clear Screen**: Type `clear`
5. **Get Help**: Type `help` in REPL

## Next Steps

- Read the full [README.md](README.md) for comprehensive documentation
- Explore [examples/config/example-config.yml](examples/config/example-config.yml) for advanced configuration
- Check out the [nodi_prompt.md](nodi_prompt.md) for complete feature list

## Troubleshooting

### Config not found

```bash
nodi init
```

### Invalid service/environment

```bash
nodi validate
nodi services
nodi envs
```

### Connection errors

Check your `.env` file and API keys.

### Import errors

```bash
pip install -e .
# Or with all dependencies
pip install -e .[full]
```

## Support

For issues and questions, please visit: https://github.com/yourusername/nodi/issues
