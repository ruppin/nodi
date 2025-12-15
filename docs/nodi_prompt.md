# Nodi - Interactive Data Query Tool

## Project Name: `nodi` (ನೋಡಿ)

**Etymology**: Kannada word meaning "look" or "see" (imperative form)
**Pronunciation**: "no-dee"
**Tagline**: "Nodi - Look at your data"

## Overview

Build a **Python-based interactive data query tool** designed for **microservices architectures** with multiple services across multiple environments (dev/qa/prod). While primarily focused on REST APIs, the tool uses a **provider-based architecture** that allows extension to databases, log tools, message queues, and other data sources. The tool provides a REPL interface for quickly testing and exploring data sources with succinct `service.environment@endpoint` syntax, built-in jq filtering, and environment-aware configuration.

**Note**: The tool starts with REST API support and can be extended to other data sources through providers (see [REST_CLIENT_EXTENSIBILITY.md](REST_CLIENT_EXTENSIBILITY.md)).

## Target Users

- Backend developers testing microservices across environments
- DevOps engineers monitoring multi-environment deployments
- QA engineers validating services in dev/qa/prod
- API consumers working with multiple services
- Anyone who prefers command-line tools over Postman/Insomnia

## Core Architecture

### Service-Environment Model

The tool is designed around:
- **Multiple Services**: user-service, order-service, payment-service, etc.
- **Multiple Environments**: dev, qa, prod (configurable)
- **Shared Aliases**: Same endpoint paths across all environments
- **Header Management**: Per-environment headers (API keys, cookies, custom headers)
- **Certificate Management**: Shared dev/qa certs, separate prod certs

### Key Innovation: Succinct Syntax

```bash
# Format: service.environment@endpoint
nodi user-service.dev@users
nodi order-service.qa@order:123
nodi payment-service.prod@payments

# Default environment (dev)
nodi user-service@users  # Uses default env

# Multi-environment testing
nodi --compare dev,qa user-service@user:123

# Multi-service testing
nodi --all-services prod@/health --table
```

## Core Features

### 1. REPL Interface

**Interactive Shell:**
- Launch with `nodi` command to enter interactive mode
- Service and environment context displayed in prompt: `[user-service.dev]>`
- Auto-completion for services, environments, aliases, and commands
- Command history with up/down arrow navigation
- Multi-line input support for request bodies
- Syntax highlighting for JSON/XML responses
- Tab completion for services, environments, and aliases

**Session Management:**
- Current service and environment context
- Quick switching: `env qa`, `service order-service`
- One-off requests: `order-service.prod@orders`
- Header state per session
- Auto-save recent requests

**Example REPL session:**
```
$ nodi

nodi> services
Available services:
  user-service    → dev, qa, prod
  order-service   → dev, qa, prod
  payment-service → dev, qa, prod

nodi> use user-service.dev
Service: user-service
Environment: dev
Base URL: https://user-service.dev.company.com

nodi [user-service.dev]> users | jq length
GET https://user-service.dev.company.com/api/v1/users
Status: 200 OK
42

nodi [user-service.dev]> user:5 | jq .name
GET https://user-service.dev.company.com/api/v1/users/5
Status: 200 OK
"Jane Smith"

nodi [user-service.dev]> env qa
Environment: qa

nodi [user-service.qa]> users | jq length
GET https://user-service.qa.company.com/api/v1/users
Status: 200 OK
38

nodi [user-service.qa]> service order-service

nodi [order-service.qa]> orders
GET https://order-service.qa.company.com/api/v1/orders
Status: 200 OK
[...]
```

### 2. Configuration Management

**Configuration File Structure (`~/.nodi/config.yml`):**

```yaml
# Define services with base URLs per environment
services:
  user-service:
    dev:
      base_url: https://user-service.dev.company.com
    qa:
      base_url: https://user-service.qa.company.com
    prod:
      base_url: https://user-service.prod.company.com
    # Aliases are shared across all environments
    aliases:
      users: /api/v1/users
      user: /api/v1/users/{id}
      profile: /api/v1/users/{id}/profile
      search: /api/v1/users/search

  order-service:
    dev:
      base_url: https://order-service.dev.company.com
    qa:
      base_url: https://order-service.qa.company.com
    prod:
      base_url: https://order-service.prod.company.com
    aliases:
      orders: /api/v1/orders
      order: /api/v1/orders/{id}
      status: /api/v1/orders/{id}/status

# Headers per environment (applies to all services)
headers:
  dev:
    X-API-Key: ${DEV_API_KEY}
    X-Environment: development
    Cookie: session=${DEV_SESSION_COOKIE}
  qa:
    X-API-Key: ${QA_API_KEY}
    X-Environment: qa
    Cookie: session=${QA_SESSION_COOKIE}
  prod:
    X-API-Key: ${PROD_API_KEY}
    X-Environment: production
    Cookie: session=${PROD_SESSION_COOKIE}

# SSL certificates
certificates:
  dev:
    cert: ~/.certs/dev-qa.crt
    key: ~/.certs/dev-qa.key
    ca: ~/.certs/dev-qa-ca.crt
    verify: true
  qa:
    cert: ~/.certs/dev-qa.crt
    key: ~/.certs/dev-qa.key
    ca: ~/.certs/dev-qa-ca.crt
    verify: true
  prod:
    cert: ~/.certs/prod.crt
    key: ~/.certs/prod.key
    ca: ~/.certs/prod-ca.crt
    verify: true

# Default settings
default_environment: dev
default_service: user-service

# Service aliases (optional short names)
service_aliases:
  us: user-service
  os: order-service
  ps: payment-service
```

**Configuration Hierarchy:**
1. Command-line arguments (highest priority)
2. Current directory `.nodi.yml`
3. Parent directories (up to git root)
4. User config `~/.nodi/config.yml`
5. System config `/etc/nodi/config.yml`

**Environment Variables:**
- All `${VAR}` placeholders replaced with environment variables
- Support for `.env` file loading
- Dynamic variable substitution

### 3. HTTP Methods Support

**Standard Methods:**
- `GET`, `POST`, `PUT`, `PATCH`, `DELETE`, `HEAD`, `OPTIONS`
- Custom HTTP methods support

**Request Features:**
- URL parameters: `get users?page=2&per_page=50`
- Path variables: `user:123` expands to `/api/v1/users/123`
- Query shortcuts: `search q=john status=active`
- Request body from file: `post users @request.json`
- Request body from stdin: `post users < data.json`
- Inline JSON: `post users {"name": "test"}`
- Form data: `post /login --form username=admin password=secret`
- File uploads: `post /upload --file document.pdf`

**Examples:**
```bash
# In CLI mode
nodi user-service.dev@users
nodi user-service.dev@user:123
nodi user-service.dev@search q=john limit=10
nodi order-service.qa@post:orders {"item": "book", "qty": 2}

# In REPL mode
nodi [user-service.dev]> users
nodi [user-service.dev]> user:123
nodi [user-service.dev]> search q=john status=active
nodi [user-service.dev]> post users {"name": "John", "email": "john@example.com"}
```

### 4. Multi-Environment & Multi-Service Testing

**Multi-Environment Operations:**
```bash
# Test across all environments
nodi --all-envs user-service@users

# Test across specific environments
nodi --envs dev,qa,prod user-service@users

# Compare responses
nodi --compare dev,qa user-service@user:123

# Parallel execution with table output
nodi --parallel dev,qa,prod user-service@users --table
```

**Multi-Service Operations:**
```bash
# Test across all services in prod
nodi --all-services prod@/health --table

# Specific services
nodi --services user-service,order-service qa@/api/version

# Compare across services
nodi --compare-services user-service,order-service dev@/health
```

**Combined Operations:**
```bash
# Health check across ALL services and ALL environments
nodi --all-services --all-envs /health --table

# Output:
┌──────────────────────────────┬────────┬──────────┬─────────┐
│ Service.Environment          │ Status │ Time     │ Version │
├──────────────────────────────┼────────┼──────────┼─────────┤
│ user-service.dev             │ 200    │ 45ms     │ 2.6.0   │
│ user-service.qa              │ 200    │ 52ms     │ 2.6.0   │
│ user-service.prod            │ 200    │ 98ms     │ 2.5.1   │
│ order-service.dev            │ 200    │ 41ms     │ 2.6.0   │
│ order-service.qa             │ 200    │ 48ms     │ 2.6.0   │
│ order-service.prod           │ 200    │ 105ms    │ 2.5.1   │
└──────────────────────────────┴────────┴──────────┴─────────┘
```

### 5. jq-style JSON Filtering

**Built-in JSON Filtering:**
- Pipe responses through jq-compatible filters
- Support for jq syntax: `.field`, `.array[]`, `.nested.value`
- Array filtering: `.items[] | select(.status == "active")`
- Transformations: `.users | map({name, email})`
- Built-in filters: `keys`, `values`, `length`, `type`

**Filter Examples:**
```bash
# Extract single field
nodi user-service.dev@user:123 | jq .name

# Extract from array
nodi user-service.dev@users | jq .[0].name

# Filter array elements
nodi order-service.qa@orders | jq '.[] | select(.status == "pending")'

# Transform data
nodi user-service.dev@users | jq 'map({name, email})'

# Count items
nodi order-service.prod@orders | jq length

# Complex filter
nodi user-service.dev@users | jq '.[] | select(.role == "admin") | .name'
```

**CSV/Table Output:**
- `--table` flag to display JSON as ASCII table
- `--csv` flag to export as CSV
- Automatic column detection from JSON arrays

**Examples:**
```bash
nodi user-service.dev@users | jq '.[] | {name, email, role}' --table
nodi order-service.qa@orders | jq '.[] | {id, status, total}' --csv > orders.csv
```

### 6. Header Management

**Header Configuration:**
- Per-environment headers (global)
- Per-service headers (overrides environment)
- Per-request headers (overrides all)

**Header Priority (highest to lowest):**
1. Request-specific headers (command line: `-H`)
2. Service-specific headers (in config)
3. Environment-wide headers (in config)
4. Global default headers

**Header Operations:**
```bash
# View current headers
nodi [user-service.dev]> headers
Current headers (user-service.dev):
  X-API-Key: dev-key-*** (masked)
  X-Environment: development
  Cookie: session=*** (masked)

# Add header for session
nodi [user-service.dev]> set-header X-Trace-ID test-123

# Remove header
nodi [user-service.dev]> unset-header X-Trace-ID

# One-off header
nodi -H "X-Debug: true" user-service.dev@users
```

**Cookie Management:**
```bash
# Cookies in headers configuration
headers:
  dev:
    Cookie: session=${DEV_SESSION_COOKIE}

# Dynamic cookies
nodi --cookie "session=xyz123" user-service.dev@users
nodi --cookie-jar cookies.txt user-service.dev@users
nodi --save-cookies cookies.txt user-service.dev@login
```

### 7. Certificate Management

**Per-Environment Certificates:**
- Dev and QA share certificates
- Production has separate certificates
- Per-request certificate override
- SSL verification control

**Configuration:**
```yaml
certificates:
  dev:
    cert: ~/.certs/dev-qa.crt
    key: ~/.certs/dev-qa.key
    ca: ~/.certs/dev-qa-ca.crt
    verify: true
  prod:
    cert: ~/.certs/prod.crt
    key: ~/.certs/prod.key
    ca: ~/.certs/prod-ca.crt
    verify: true
    ssl_version: TLSv1.2
```

**Usage:**
```bash
# Use configured certificates (automatic)
nodi user-service.dev@users

# Override certificate
nodi --cert custom.crt --key custom.key user-service.dev@users

# Disable SSL verification (debug only)
nodi --no-verify user-service.dev@users
```

### 8. Response Handling

**Response Display:**
- Pretty-printed JSON with syntax highlighting
- XML formatting and highlighting
- HTML rendering options (raw or formatted)
- Binary data detection and handling
- Streaming responses for large payloads

**Response Information:**
- Status code and reason
- Response headers (toggleable display)
- Response time
- Response size
- Content type detection

**Response Saving:**
```bash
# Save to file
nodi user-service.dev@users > users.json

# Append to file
nodi user-service.dev@users >> all-data.json

# Download binary
nodi file-service.prod@/files/report.pdf > report.pdf

# Stream large response
nodi log-service.dev@/logs --stream
```

**Verbose Mode:**
```bash
# Show full request/response details
nodi --verbose user-service.dev@users
# Output:
# GET https://user-service.dev.company.com/api/v1/users
#
# Request Headers:
#   X-API-Key: dev-key-***
#   X-Environment: development
#   User-Agent: nodi/1.0
#
# Response: 200 OK (145ms)
# Response Headers:
#   Content-Type: application/json
#   Content-Length: 1234
#
# {
#   "users": [...]
# }
```

### 9. Request History

**History Management:**
- Automatic history saving
- Search history: `history search user-service`
- Replay requests: `history replay 5`
- Export history: `history export history.json`
- Clear history: `history clear`

**History Display:**
```bash
nodi [user-service.dev]> history
Recent requests:
  1. GET  user-service.dev/api/v1/users (200 OK, 145ms)
  2. GET  user-service.dev/api/v1/users/5 (200 OK, 89ms)
  3. GET  user-service.qa/api/v1/users (200 OK, 156ms)
  4. POST order-service.qa/api/v1/orders (201 Created, 234ms)
  5. GET  payment-service.prod/api/v1/payments (200 OK, 312ms)

nodi [user-service.dev]> history replay 2
Replaying: GET user-service.dev/api/v1/users/5
```

### 10. Request Collections

**Collection Management:**
- Organize related requests
- Share collections across team
- Run entire collection
- Works across all environments

**Collection File (`~/.nodi/collections/user-ops.yml`):**
```yaml
name: User Operations
service: user-service

requests:
  get-user:
    method: GET
    alias: user
    description: Get user by ID
    params:
      - id: required

  search-users:
    method: GET
    alias: search
    params:
      - q: required
      - status: optional (default: active)
      - limit: optional (default: 50)

  create-user:
    method: POST
    alias: users
    body:
      name: string
      email: string
      role: string
```

**Usage:**
```bash
# Run collection request in specific environment
nodi coll user-ops get-user dev id=123
nodi coll user-ops get-user qa id=123

# Run across all environments
nodi coll user-ops get-user --all-envs id=123 --table

# In REPL
nodi [user-service.dev]> load-collection user-ops
nodi [user-service.dev]> run get-user id=123
```

### 11. Environment Promotion Workflow

**Dev → QA → Prod Testing:**
```bash
# Test in dev
nodi user-service.dev@user:123
# {"name": "John", "status": "active"}

# Compare dev vs qa
nodi --compare dev,qa user-service@user:123
# Shows diff

# Compare qa vs prod
nodi --compare qa,prod user-service@user:123

# Check version across all environments
nodi --all-envs user-service@/api/version --table
```

**Deployment Verification:**
```bash
# Verify deployment across all services in production
nodi --all-services prod@/health --table
nodi --all-services prod@/api/version --table

# Compare QA vs Prod before promotion
nodi --compare qa,prod --all-services /api/version
```

### 12. Configuration Profiles

**Profile Management:**
- Switch between different configurations
- Team-specific profiles
- Environment-specific profiles

**Profile File (`~/.nodi/profiles.yml`):**
```yaml
profiles:
  default:
    default_environment: dev
    default_service: user-service

  production-monitoring:
    default_environment: prod
    services:
      - user-service
      - order-service
      - payment-service
    headers:
      X-Monitor-Source: ops-team

  qa-testing:
    default_environment: qa
    headers:
      X-Test-Run-ID: ${TEST_RUN_ID}
      X-Tester: ${USER}
```

**Usage:**
```bash
# Load profile
nodi --profile production-monitoring

# Switch profile in REPL
nodi> profile qa-testing
Loaded profile: qa-testing
Default environment: qa
```

### 13. Output Formats

**Supported Formats:**
- JSON (pretty-printed, colored)
- JSON (compact)
- YAML
- XML (formatted)
- Table (ASCII art)
- CSV
- Raw (no formatting)

**Format Selection:**
```bash
# Pretty JSON (default)
nodi user-service.dev@users

# Compact JSON
nodi user-service.dev@users --compact

# YAML
nodi user-service.dev@users --yaml

# Table
nodi user-service.dev@users --table

# CSV
nodi user-service.dev@users --csv

# Raw
nodi user-service.dev@users --raw
```

### 14. Diff & Compare

**Response Comparison:**
```bash
# Compare across environments
nodi --compare dev,qa user-service@user:123

# Output:
┌──────────────┬──────────────┐
│ dev          │ qa           │
├──────────────┼──────────────┤
│ {            │ {            │
│   "name": "John",           │
│   "email": "j@example.com"  │
│   "role": "admin"           │
< "version": "2.6.0"          │
│ }            > "version": "2.5.1" │
└──────────────┴──────────────┘

# Compare across services
nodi --compare-services user-service,order-service dev@/health

# Side-by-side diff
nodi --diff dev,qa user-service@user:123
```

### 15. Testing & Assertions

**Response Validation:**
```bash
# Assert status code
nodi user-service.dev@users --assert-status 200

# Assert response contains
nodi user-service.dev@user:123 --assert-contains "John"

# Assert JSON field
nodi user-service.dev@user:123 --assert-field .status=active

# Assert response time
nodi user-service.dev@users --assert-time-lt 500ms

# Multiple assertions
nodi user-service.dev@users \
  --assert-status 200 \
  --assert-field '.length >= 10' \
  --assert-time-lt 1000ms
```

**Test Scripts:**
```bash
# Run test script
nodi --test user-service-tests.yml

# Test script format
# user-service-tests.yml
tests:
  - name: Get user by ID
    request:
      service: user-service
      environment: dev
      endpoint: user:123
    assertions:
      - status: 200
      - field: .name
        equals: "John"
      - time_lt: 500ms

  - name: Search users
    request:
      service: user-service
      environment: qa
      endpoint: search
      params:
        q: john
    assertions:
      - status: 200
      - field: .results
        type: array
      - field: '.results | length'
        gte: 1
```

### 16. Batch Mode / Scripting

**Non-Interactive Execution:**
```bash
# Single request
nodi user-service.dev@users

# With output redirection
nodi user-service.dev@users > users.json

# Multiple requests
nodi user-service.dev@users && \
nodi order-service.dev@orders && \
nodi payment-service.dev@payments

# From script file
nodi --script requests.txt

# requests.txt:
# user-service.dev@users
# user-service.dev@user:123
# order-service.qa@orders
```

**Exit Codes:**
- `0`: Success (2xx response)
- `1`: Client error (4xx response)
- `2`: Server error (5xx response)
- `3`: Network error
- `4`: Configuration error
- `5`: Assertion failed

### 17. Export Capabilities

**Export Formats:**
```bash
# Export as curl command
nodi user-service.dev@users --export-curl
# Output: curl -X GET 'https://user-service.dev.company.com/api/v1/users' \
#   -H 'X-API-Key: dev-key-xxx' \
#   -H 'X-Environment: development'

# Export as Python code
nodi user-service.dev@users --export-python
# Output: import requests
#         response = requests.get(
#             'https://user-service.dev.company.com/api/v1/users',
#             headers={'X-API-Key': 'dev-key-xxx', ...}
#         )

# Export as Postman collection
nodi --export-postman user-ops.json

# Export collection
nodi coll user-ops --export-postman user-ops-collection.json
```

### 18. Performance Monitoring

**Request Metrics:**
```bash
# Show timing breakdown
nodi user-service.dev@users --timing
# Output:
# DNS Lookup:     12ms
# TCP Connect:    23ms
# TLS Handshake:  45ms
# Request:        5ms
# Response:       60ms
# Total:          145ms

# Benchmark endpoint
nodi user-service.dev@users --bench 100
# Run 100 requests and show statistics
# Output:
# Requests: 100
# Success:  100 (100%)
# Failed:   0
# Avg time: 145ms
# Min time: 89ms
# Max time: 312ms
# P50:      142ms
# P95:      198ms
# P99:      289ms
```

### 19. Plugin System

**Plugin Support:**
- Custom authentication methods
- Custom response formatters
- Custom validators
- Pre/post-request hooks

**Plugin Example:**
```python
# ~/.nodi/plugins/custom_auth.py
from nodi.plugin import Plugin

class CustomAuthPlugin(Plugin):
    def pre_request(self, request):
        # Add custom authentication
        request.headers['X-Custom-Auth'] = self.generate_token()
        return request

    def generate_token(self):
        # Custom token generation logic
        return "custom-token-123"
```

**Usage:**
```yaml
# In config.yml
plugins:
  - custom_auth
  - request_logger
  - response_validator
```

## Technical Implementation

### Technology Stack

**Core:**
- **Python 3.8+**: Main language
- **httpx**: HTTP client with async support, HTTP/2
- **pyyaml**: Configuration file parsing
- **python-dotenv**: Environment variable management

**REPL:**
- **prompt_toolkit**: Advanced REPL with auto-completion
- **pygments**: Syntax highlighting

**JSON Processing:**
- **jq** (via `pyjq`): JSON filtering
- **jsonpath-ng**: Alternative JSON queries

**Output Formatting:**
- **rich**: Beautiful terminal output, tables, colors
- **tabulate**: Simple table formatting (fallback)

**Security:**
- **cryptography**: SSL/TLS handling
- **keyring**: Secure credential storage

**Optional:**
- **pandas**: Advanced CSV/table operations
- **pydantic**: Configuration validation

### Project Structure

```
nodi/
├── nodi/
│   ├── __init__.py
│   ├── __main__.py          # Entry point
│   ├── cli.py               # CLI argument parsing
│   ├── repl.py              # Interactive REPL
│   ├── client.py            # HTTP client wrapper (deprecated - moved to providers)
│   ├── config.py            # Configuration management
│   │   ├── loader.py        # Config file loading
│   │   ├── validator.py     # Config validation
│   │   └── models.py        # Config data models
│   ├── environment.py       # Environment management
│   │   ├── manager.py       # Service/environment switching
│   │   ├── resolver.py      # URL resolution (service.env@endpoint)
│   │   └── headers.py       # Header management
│   ├── providers/           # Provider system (extensibility layer)
│   │   ├── __init__.py
│   │   ├── base.py          # DataProvider base class
│   │   ├── manager.py       # ProviderManager
│   │   ├── rest.py          # REST/HTTP provider (built-in)
│   │   ├── mongodb.py       # MongoDB provider (optional)
│   │   ├── postgres.py      # PostgreSQL provider (optional)
│   │   ├── splunk.py        # Splunk provider (optional)
│   │   └── elasticsearch.py # Elasticsearch provider (optional)
│   ├── certificates.py      # Certificate handling
│   ├── filters.py           # jq integration
│   ├── formatters.py        # Response formatting
│   │   ├── json.py
│   │   ├── yaml.py
│   │   ├── table.py
│   │   └── csv.py
│   ├── history.py           # Request history
│   ├── collections.py       # Request collections
│   ├── comparison.py        # Multi-env/service comparison
│   ├── testing.py           # Assertions and test runner
│   ├── export.py            # Export to curl/Python/Postman
│   ├── monitoring.py        # Performance metrics
│   ├── plugins/             # Plugin system
│   │   ├── __init__.py
│   │   ├── base.py
│   │   └── loader.py
│   └── utils/
│       ├── color.py
│       ├── prompt.py
│       └── validators.py
├── tests/
│   ├── test_config.py
│   ├── test_environment.py
│   ├── test_providers.py    # Provider tests
│   ├── test_rest_provider.py
│   ├── test_repl.py
│   └── test_comparison.py
├── docs/
│   ├── REST_CLIENT_PROJECT_PROMPT.md
│   ├── REST_CLIENT_ENHANCED_URLS.md
│   ├── REST_CLIENT_EXTENSIBILITY.md  # Provider architecture
│   └── provider_development.md
├── examples/
│   ├── config.yml
│   ├── collections/
│   ├── plugins/
│   │   └── custom_provider/  # Example custom provider
│   └── providers/
│       ├── redis_provider.py
│       └── kafka_provider.py
├── setup.py
├── pyproject.toml
├── requirements.txt
├── requirements-providers.txt  # Optional provider dependencies
├── README.md
└── LICENSE
```

### Core Classes

**Configuration Management:**
```python
from dataclasses import dataclass
from typing import Dict, List, Optional

@dataclass
class ServiceEnvironment:
    base_url: str
    headers: Optional[Dict[str, str]] = None

@dataclass
class Service:
    name: str
    environments: Dict[str, ServiceEnvironment]  # dev, qa, prod
    aliases: Dict[str, str]  # endpoint aliases

@dataclass
class EnvironmentHeaders:
    headers: Dict[str, str]

@dataclass
class Certificates:
    cert: Optional[str]
    key: Optional[str]
    ca: Optional[str]
    verify: bool = True

@dataclass
class Config:
    services: Dict[str, Service]
    headers: Dict[str, EnvironmentHeaders]  # per environment
    certificates: Dict[str, Certificates]  # per environment
    default_environment: str
    default_service: Optional[str]
    service_aliases: Optional[Dict[str, str]]
```

**URL Resolution:**
```python
class URLResolver:
    """Resolves service.env@endpoint syntax to full URLs."""

    def parse(self, input: str) -> RequestSpec:
        """
        Parse: service.env@endpoint
        Returns: RequestSpec with service, environment, path
        """
        pass

    def resolve(self, spec: RequestSpec, config: Config) -> str:
        """Resolve to full URL with alias expansion."""
        pass
```

**Environment Manager:**
```python
class EnvironmentManager:
    """Manages current service and environment context."""

    def __init__(self, config: Config):
        self.config = config
        self.current_service = config.default_service
        self.current_environment = config.default_environment

    def switch_service(self, service: str):
        """Switch to different service."""
        pass

    def switch_environment(self, env: str):
        """Switch to different environment."""
        pass

    def get_headers(self) -> Dict[str, str]:
        """Get merged headers for current context."""
        pass

    def get_certificates(self) -> Certificates:
        """Get certificates for current environment."""
        pass
```

**HTTP Client:**
```python
import httpx

class RestClient:
    """HTTP client with service-environment awareness."""

    def __init__(self, env_manager: EnvironmentManager):
        self.env_manager = env_manager
        self.session = httpx.Client()

    def request(
        self,
        method: str,
        spec: RequestSpec,
        data: Optional[dict] = None,
        **kwargs
    ) -> Response:
        """Execute HTTP request with proper headers/certs."""
        pass

    def multi_environment_request(
        self,
        method: str,
        spec: RequestSpec,
        environments: List[str],
        **kwargs
    ) -> Dict[str, Response]:
        """Execute same request across multiple environments."""
        pass

    def multi_service_request(
        self,
        method: str,
        endpoint: str,
        services: List[str],
        environment: str,
        **kwargs
    ) -> Dict[str, Response]:
        """Execute same request across multiple services."""
        pass
```

**REPL:**
```python
from prompt_toolkit import PromptSession
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.completion import WordCompleter

class RestCliRepl:
    """Interactive REPL for REST client."""

    def __init__(self, config: Config):
        self.config = config
        self.env_manager = EnvironmentManager(config)
        self.client = RestClient(self.env_manager)
        self.session = PromptSession()

    def get_prompt(self) -> str:
        """Get prompt with current context."""
        service = self.env_manager.current_service
        env = self.env_manager.current_environment
        return f"nodi [{service}.{env}]> "

    def run(self):
        """Main REPL loop."""
        while True:
            try:
                command = self.session.prompt(
                    self.get_prompt(),
                    auto_suggest=AutoSuggestFromHistory(),
                    completer=self.get_completer()
                )
                self.execute(command)
            except KeyboardInterrupt:
                continue
            except EOFError:
                break
```

## Command Line Interface

### CLI Arguments

```bash
# Basic usage
nodi service.env@endpoint           # Single request
nodi                                # Enter REPL

# Service and environment
nodi --env ENV service@endpoint     # Override default environment
nodi --service SVC endpoint         # Use specific service

# Multi-environment
nodi --all-envs service@endpoint    # All environments
nodi --envs dev,qa service@endpoint # Specific environments
nodi --compare dev,qa service@endpoint  # Compare

# Multi-service
nodi --all-services env@endpoint    # All services
nodi --services s1,s2 env@endpoint  # Specific services

# HTTP methods
nodi service.env@get:endpoint
nodi service.env@post:endpoint {"data": "value"}
nodi service.env@put:endpoint @file.json
nodi service.env@delete:endpoint

# Headers
-H "Header: value"                     # Add header
--header "Header: value"               # Add header
--cookie "name=value"                  # Set cookie
--cookie-jar FILE                      # Load cookies

# Certificates
--cert FILE                            # Client certificate
--key FILE                             # Client key
--ca FILE                              # CA certificate
--no-verify                            # Disable SSL verification

# Output
--json                                 # JSON output (default)
--yaml                                 # YAML output
--table                                # Table output
--csv                                  # CSV output
--raw                                  # Raw response
--compact                              # Compact JSON
--verbose, -v                          # Verbose mode

# Filtering
| jq FILTER                            # jq filter
--filter FILTER                        # Built-in filter

# Response handling
> FILE                                 # Save to file
--save FILE                            # Save to file
--stream                               # Stream response

# Testing
--assert-status CODE                   # Assert status code
--assert-contains TEXT                 # Assert response contains
--assert-field EXPR                    # Assert JSON field
--assert-time-lt MS                    # Assert response time
--test FILE                            # Run test file

# Comparison
--compare ENV1,ENV2                    # Compare environments
--compare-services SVC1,SVC2           # Compare services
--diff ENV1,ENV2                       # Show diff

# Export
--export-curl                          # Export as curl
--export-python                        # Export as Python
--export-postman                       # Export as Postman

# Performance
--timing                               # Show timing breakdown
--bench N                              # Benchmark (N requests)

# Configuration
--config FILE                          # Config file
--profile NAME                         # Load profile
--set VAR=VALUE                        # Set variable

# Information
services                               # List services
service NAME                           # Show service details
envs                                   # List environments
env NAME                               # Show environment details
headers [ENV]                          # Show headers
history                                # Show history
version                                # Show version
help                                   # Show help
```

### REPL Commands

```bash
# Service/environment management
use service.env                        # Switch service and environment
service NAME                           # Switch service
env NAME                               # Switch environment
services                               # List services
envs                                   # List environments

# Requests
get ENDPOINT                           # GET request
post ENDPOINT [BODY]                   # POST request
put ENDPOINT [BODY]                    # PUT request
patch ENDPOINT [BODY]                  # PATCH request
delete ENDPOINT                        # DELETE request
head ENDPOINT                          # HEAD request
options ENDPOINT                       # OPTIONS request

# Aliases (shortcuts)
users                                  # Alias for /api/v1/users
user:123                               # Alias for /api/v1/users/123
orders                                 # Alias for /api/v1/orders

# Headers
headers                                # Show current headers
headers ENV                            # Show environment headers
set-header NAME VALUE                  # Set header
unset-header NAME                      # Remove header

# History
history                                # Show history
history search TEXT                    # Search history
history replay N                       # Replay request
history clear                          # Clear history

# Collections
load-collection NAME                   # Load collection
run REQUEST [PARAMS]                   # Run collection request
collections                            # List collections

# Configuration
config                                 # Show current config
profile NAME                           # Switch profile
set VAR VALUE                          # Set variable

# Utilities
clear                                  # Clear screen
exit, quit                             # Exit REPL
help                                   # Show help
```

## Installation & Setup

### Installation

```bash
# From PyPI (when published)
pip install nodi

# From source
git clone https://github.com/yourusername/nodi.git
cd nodi
pip install -e .

# With all optional dependencies
pip install nodi[full]
```

### Initial Setup

```bash
# Create config directory
mkdir -p ~/.nodi

# Create initial config
nodi init

# Edit config
nodi config edit

# Verify setup
nodi services
nodi envs
```

### Example Configuration

```yaml
# ~/.nodi/config.yml
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

certificates:
  dev:
    cert: ~/.certs/dev-qa.crt
    key: ~/.certs/dev-qa.key
  prod:
    cert: ~/.certs/prod.crt
    key: ~/.certs/prod.key

default_environment: dev
```

```bash
# Set environment variables
export DEV_API_KEY=dev-secret-key
export QA_API_KEY=qa-secret-key
export PROD_API_KEY=prod-secret-key
```

## Usage Examples

### Example 1: Quick Testing

```bash
# Single request
nodi user-service.dev@users

# With filtering
nodi user-service.dev@users | jq length

# Get specific user
nodi user-service.dev@user:123 | jq .name
```

### Example 2: Environment Comparison

```bash
# Compare user across environments
nodi --compare dev,qa,prod user-service@user:123

# Compare with diff view
nodi --diff dev,qa user-service@user:123
```

### Example 3: Multi-Service Health Check

```bash
# Health check all services in production
nodi --all-services prod@/health --table

# Version check
nodi --all-services --all-envs /api/version --table
```

### Example 4: Interactive Session

```bash
$ nodi

nodi> use user-service.dev
Service: user-service
Environment: dev

nodi [user-service.dev]> users | jq length
42

nodi [user-service.dev]> user:5
{
  "id": 5,
  "name": "Jane Smith",
  "email": "jane@example.com"
}

nodi [user-service.dev]> env qa

nodi [user-service.qa]> user:5 | jq .name
"Jane Smith"
```

### Example 5: Testing Workflow

```bash
# Run tests
nodi --test user-service-tests.yml

# With specific environment
nodi --test user-service-tests.yml --env qa

# Export results
nodi --test user-service-tests.yml --output test-results.json
```

## Benefits

✅ **Service-Oriented**: Built for microservices architecture
✅ **Environment-Aware**: Seamless dev/qa/prod workflow
✅ **Succinct Syntax**: `service.env@endpoint` is fast to type
✅ **Shared Aliases**: Define once, use everywhere
✅ **Multi-Testing**: Compare across environments and services
✅ **Header Management**: Flexible per-environment configuration
✅ **Certificate Handling**: Built-in SSL/TLS support
✅ **REPL-Friendly**: Interactive exploration
✅ **Scriptable**: Full CLI for automation
✅ **Team-Ready**: Shareable configuration
✅ **Secure**: Environment variables, certificate management

This tool perfectly fits your multi-service, multi-environment architecture and daily workflows!
