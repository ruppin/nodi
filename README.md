# Nodi (ನೋಡಿ) - Interactive Data Query Tool

**Etymology**: Kannada word meaning "look" or "see" (imperative form)
**Pronunciation**: "no-dee"
**Tagline**: "Nodi - Look at your data"

A Python-based interactive data query tool designed for **microservices architectures** with multiple services across multiple environments (dev/qa/prod). Provides a REPL interface for quickly testing and exploring REST APIs with succinct `service.environment@endpoint` syntax, built-in jq filtering, and environment-aware configuration.

## Features

- 🚀 **Succinct Syntax**: `service.env@endpoint` for fast queries
- 🔄 **Multi-Environment**: Seamlessly switch between dev/qa/prod
- 🎯 **Service-Oriented**: Built for microservices architecture
- 💻 **Interactive REPL**: Explore APIs interactively with auto-completion
- 🔍 **jq Filtering**: Built-in JSON filtering and transformation
- 📊 **Multiple Formats**: JSON, YAML, Table, CSV output
- 🔐 **Header Management**: Per-environment headers and certificates
- 📜 **Request History**: Track and replay requests
- ⚡ **Fast & Lightweight**: Quick startup, minimal dependencies

## Installation

### From Source

```bash
git clone https://github.com/yourusername/nodi.git
cd nodi
pip install -e .
```

### With Optional Dependencies

```bash
# Full installation with all features (excluding jq on Windows)
pip install -e .[full]

# Development installation
pip install -e .[dev]

# Optional: Advanced jq filtering (may fail on Windows)
pip install -e .[jq]
```

**Note on jq filtering**: The `pyjq` library requires C compilation and may fail on Windows. Nodi includes built-in simple filtering that works without `pyjq`. If `pyjq` installation fails, you can still use basic filters like `.field`, `.[]`, `length`, `keys`, etc.

## Quick Start

### 1. Initialize Configuration

```bash
nodi init
```

This creates `~/.nodi/config.yml` with example configuration.

### 2. Configure Your Services

Edit `~/.nodi/config.yml`:

```yaml
services:
  user-service:
    dev:
      base_url: https://user-service.dev.company.com
    qa:
      base_url: https://user-service.qa.company.com
    prod:
      base_url: https://user-service.prod.company.com
    aliases:
      users: /api/v1/users
      user: /api/v1/users/{id}

headers:
  dev:
    X-API-Key: ${DEV_API_KEY}
  qa:
    X-API-Key: ${QA_API_KEY}
  prod:
    X-API-Key: ${PROD_API_KEY}

default_environment: dev
default_service: user-service
```

### 3. Set Environment Variables

Create `.env` file:

```bash
DEV_API_KEY=your-dev-api-key
QA_API_KEY=your-qa-api-key
PROD_API_KEY=your-prod-api-key
```

### 4. Start Using Nodi

#### Interactive REPL Mode

```bash
$ nodi

nodi [user-service.dev]> users
Status: 200 (145ms)

[
  {"id": 1, "name": "John Doe"},
  {"id": 2, "name": "Jane Smith"}
]

nodi [user-service.dev]> user:1
Status: 200 (89ms)

{
  "id": 1,
  "name": "John Doe",
  "email": "john@example.com"
}

nodi [user-service.dev]> env qa

nodi [user-service.qa]> users
Status: 200 (156ms)
...
```

#### Command Line Mode

```bash
# Single request
nodi request user-service.dev@users

# With filtering
nodi request user-service.dev@users --filter '.[] | .name'

# Different output formats
nodi request user-service.dev@users --format table
nodi request user-service.dev@users --format yaml

# Custom HTTP method
nodi request user-service.dev@users --method POST --data '{"name": "Alice"}'
```

## Usage Guide

### Syntax

The core syntax is: `service.environment@endpoint`

```bash
# Format
service.environment@[method:]endpoint[?params]

# Examples
user-service.dev@users              # GET users in dev
user-service.qa@user:123            # GET user with ID 123 in QA
order-service.prod@orders?limit=10  # GET orders with query params
payment-service.dev@post:payments   # POST to payments in dev
```

### REPL Commands

#### Service/Environment Management

```bash
services              # List all services
envs                  # List environments
use <service>.<env>   # Switch service and environment
service <name>        # Switch to service
env <name>            # Switch to environment
```

#### Making Requests

```bash
get <endpoint>        # GET request
post <endpoint>       # POST request
put <endpoint>        # PUT request
patch <endpoint>      # PATCH request
delete <endpoint>     # DELETE request

# Examples
users                 # Uses alias 'users'
user:123             # Uses alias 'user' with ID parameter
search q=john        # Passes query parameters
```

#### Headers

```bash
headers                      # Show current headers
set-header <name> <value>   # Set session header
unset-header <name>         # Remove session header
```

#### Output Formatting

```bash
format json          # Set output to JSON (default)
format yaml          # Set output to YAML
format table         # Set output to ASCII table
```

#### History

```bash
history              # Show request history
history clear        # Clear history
```

#### Other

```bash
clear                # Clear screen
help                 # Show help
exit, quit           # Exit REPL
```

### Filtering with jq

Nodi supports jq-style filtering (the `jq` keyword is optional):

```bash
# In REPL - both syntaxes work
users | jq length              # With 'jq' keyword
users | length                 # Without 'jq' keyword (cleaner!)
users | .[0].name             # Get first user's name
users | .address.city         # Nested field access

# Built-in filters (no pyjq required):
# - length, keys, values, type
# - .field, .[n], .[], .a.b.c, .[0].field

# In CLI
nodi request user-service.dev@users --filter 'length'
nodi request user-service.dev@users --filter '.[0].name'

# See FILTER_EXAMPLES.md for complete filter guide
```

### Output Formats

#### JSON (default)

```bash
nodi request user-service.dev@users
```

#### YAML

```bash
nodi request user-service.dev@users --format yaml
```

#### Table

```bash
nodi request user-service.dev@users --format table

┌────┬───────────┬─────────────────────┐
│ id │ name      │ email               │
├────┼───────────┼─────────────────────┤
│ 1  │ John Doe  │ john@example.com    │
│ 2  │ Jane Smith│ jane@example.com    │
└────┴───────────┴─────────────────────┘
```

#### CSV

```bash
nodi request user-service.dev@users --format csv > users.csv
```

## Configuration

### Configuration Hierarchy

Nodi loads configuration from multiple sources (highest to lowest priority):

1. Command-line arguments
2. Current directory `.nodi.yml`
3. Parent directories (up to git root)
4. User config `~/.nodi/config.yml`
5. System config `/etc/nodi/config.yml` (Unix only)

### Configuration File Structure

```yaml
services:
  service-name:
    environment-name:
      base_url: https://api.example.com
      timeout: 30
      verify_ssl: true
    aliases:
      alias-name: /path/to/endpoint
      parameterized: /path/{id}/resource

headers:
  environment-name:
    Header-Name: Header-Value
    X-API-Key: ${ENV_VAR}

certificates:
  environment-name:
    cert: ~/.certs/cert.crt
    key: ~/.certs/key.key
    ca: ~/.certs/ca.crt
    verify: true

default_environment: dev
default_service: my-service

service_aliases:
  short: full-service-name
```

### Environment Variables

Use `${VAR_NAME}` syntax in configuration:

```yaml
headers:
  dev:
    X-API-Key: ${DEV_API_KEY}
    Cookie: session=${DEV_SESSION}
```

Nodi automatically loads `.env` files.

## Advanced Features

### Path Parameters

Aliases can include parameters:

```yaml
aliases:
  user: /api/v1/users/{id}
  profile: /api/v1/users/{id}/profile
```

Use with `:` syntax:

```bash
user:123        # Expands to /api/v1/users/123
profile:123     # Expands to /api/v1/users/123/profile
```

### Custom Headers

```bash
# In REPL
set-header X-Custom-Header my-value

# In CLI
nodi request user-service.dev@users -H "X-Custom-Header: my-value"
```

### SSL Certificates

Configure per-environment certificates:

```yaml
certificates:
  prod:
    cert: ~/.certs/prod.crt
    key: ~/.certs/prod.key
    ca: ~/.certs/ca.crt
    verify: true
```

## CLI Commands

```bash
# Start REPL (default)
nodi
nodi repl

# Execute single request
nodi request <service.env@endpoint>

# List services
nodi services

# List environments
nodi envs
nodi envs <service-name>

# Initialize configuration
nodi init

# Validate configuration
nodi validate

# Show version
nodi --version
```

## Project Structure

```
nodi/
├── nodi/
│   ├── __init__.py
│   ├── __main__.py
│   ├── cli.py              # CLI interface
│   ├── repl.py             # Interactive REPL
│   ├── config/             # Configuration management
│   │   ├── loader.py
│   │   ├── models.py
│   │   └── validator.py
│   ├── environment/        # Environment management
│   │   ├── manager.py
│   │   ├── resolver.py
│   │   └── headers.py
│   ├── providers/          # Provider system
│   │   ├── base.py
│   │   ├── manager.py
│   │   └── rest.py
│   ├── formatters/         # Output formatters
│   │   ├── json.py
│   │   ├── yaml_fmt.py
│   │   ├── table.py
│   │   └── csv_fmt.py
│   ├── filters.py          # jq filtering
│   ├── history.py          # Request history
│   ├── certificates.py     # Certificate management
│   └── utils/              # Utilities
├── examples/
│   └── config/
│       └── example-config.yml
├── tests/
├── README.md
└── pyproject.toml
```

## Development

### Setup Development Environment

```bash
# Clone repository
git clone https://github.com/yourusername/nodi.git
cd nodi

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode
pip install -e .[dev]
```

### Run Tests

```bash
pytest
pytest --cov=nodi
```

### Code Formatting

```bash
black nodi/
flake8 nodi/
mypy nodi/
```

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

MIT License - see LICENSE file for details

## Roadmap

- [ ] Multi-environment comparison
- [ ] Request collections
- [ ] Testing and assertions
- [ ] Export to curl/Python/Postman
- [ ] Performance benchmarking
- [ ] Plugin system
- [ ] Additional data providers (MongoDB, PostgreSQL, etc.)

## Support

- Issues: https://github.com/yourusername/nodi/issues
- Documentation: https://github.com/yourusername/nodi/docs

## Acknowledgments

- Inspired by tools like HTTPie, Postman, and curl
- Built with httpx, prompt_toolkit, and rich
