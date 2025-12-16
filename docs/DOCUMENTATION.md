# Nodi Documentation

Complete guide to Nodi features, configuration, and troubleshooting.

## Table of Contents

### Quick Workflows
- [Getting Started](#getting-started)
- [Common Use Cases](#common-use-cases)
- [Quick Workflows](#quick-workflows-1)

### Core Features
- [Configuration](#configuration)
- [HTTP Requests](#http-requests)
- [Path Parameters](#path-parameters)
- [Query Parameters](#query-parameters)
- [Headers](#headers)
- [Variables](#variables)
- [Filters](#filters)
- [Projections](#projections)
- [Scripting](#scripting)
- [SSL/TLS Certificates](#ssltls-certificates)

### Reference
- [Configuration Reference](#configuration-reference)
- [Syntax Reference](#syntax-reference)
- [Filter Reference](#filter-reference)
- [Troubleshooting](#troubleshooting)

---

# Quick Workflows

## Getting Started

### 1. Initialize Nodi

```bash
nodi init
```

This creates `~/.nodi/config.yml`.

### 2. Add Your First Service

Edit `~/.nodi/config.yml`:

```yaml
services:
  jsonplaceholder:
    dev:
      base_url: https://jsonplaceholder.typicode.com
    aliases:
      posts: /posts
      post: /posts/{id}
      users: /users
      user: /users/{id}

default_service: jsonplaceholder
default_environment: dev
```

### 3. Test Your Setup

```bash
nodi validate
nodi repl
```

```bash
nodi [jsonplaceholder.dev]> posts
# Returns list of posts

nodi [jsonplaceholder.dev]> post:1
# Returns post with ID 1
```

---

## Common Use Cases

### Use Case 1: API Development Testing

**Scenario**: Test your API during development

```yaml
# config.yml
services:
  myapp:
    dev:
      base_url: http://localhost:3000
    staging:
      base_url: https://staging.myapp.com
    prod:
      base_url: https://api.myapp.com
    aliases:
      health: /health
      users: /api/users
      user: /api/users/{id}
```

**Workflow**:
```bash
# Start REPL
nodi repl

# Test health endpoint
nodi> health

# Get all users
nodi> users

# Get specific user
nodi> user:123

# Switch to staging
nodi> env staging
nodi> users

# Create user
nodi> post users {"name": "John", "email": "john@example.com"}
```

### Use Case 2: Multi-User Testing

**Scenario**: Test API with different user sessions

```yaml
# config.yml
variables:
  user1_session: "sid=abc123"
  user2_session: "sid=xyz789"
  admin_session: "sid=admin000"

headers:
  dev:
    Cookie: ${var:user1_session}  # Default session
```

**Workflow**:
```bash
# Test as user 1 (default)
nodi> get profile
{"user_id": 1, "name": "John"}

# Test as user 2 (inline override)
nodi> get profile -H Cookie:$user2_session
{"user_id": 2, "name": "Jane"}

# Test as admin
nodi> get /admin/dashboard -H Cookie:$admin_session
{...}
```

### Use Case 3: Automated Testing

**Scenario**: Create automated test scripts

**Script** (`test_api.nodi`):
```nodi
# Test user API
echo "Testing user API..."

# Get all users
GET users | @count
$count = $data
assert $count > 0

# Get first user
GET user:1
$user = $data
assert $user.id == 1
assert $user.email != null

echo "All tests passed!"
```

**Run**:
```bash
nodi> run test_api.nodi
Testing user API...
All tests passed!
```

---

# Core Features

## Configuration

### Configuration File Structure

Nodi uses `~/.nodi/config.yml` as the main configuration file:

```yaml
# Service definitions
services:
  service-name:
    environment-name:
      base_url: https://api.example.com
      verify_ssl: true
      timeout: 30
      http2: false
    aliases:
      endpoint-name: /api/path
      parameterized: /api/path/{param}

# Global headers (applied to all environments)
headers:
  environment-name:
    Header-Name: value
    Auth-Header: ${ENV_VAR}

# Variables (used in headers and scripts)
variables:
  var_name: value
  token: ${AUTH_TOKEN}

# Predefined filters
filters:
  filter-name: "jq expression"
  emails: ".[*].email"

# Predefined projections
projections:
  projection-name:
    - field1
    - field2

# Defaults
default_service: service-name
default_environment: environment-name

# SSL/TLS certificates
certificates:
  cert_file: /path/to/cert.pem
  key_file: /path/to/key.pem
  ca_bundle: /path/to/ca-bundle.crt
```

### Service Configuration

Define multiple services and environments:

```yaml
services:
  # Internal API
  internal-api:
    dev:
      base_url: http://localhost:8000
      verify_ssl: false
    staging:
      base_url: https://staging-internal.company.com
      verify_ssl: true
    prod:
      base_url: https://internal.company.com
      verify_ssl: true
    aliases:
      users: /api/v1/users
      user: /api/v1/users/{id}

  # External API
  external-api:
    dev:
      base_url: https://api-sandbox.partner.com
    prod:
      base_url: https://api.partner.com
    aliases:
      orders: /v2/orders
      order: /v2/orders/{orderId}
```

### Environment Variables

Use environment variables in configuration:

**1. Create `.env` file**:
```bash
# .env
DEV_API_KEY=dev_key_12345
PROD_API_KEY=prod_key_67890
AUTH_TOKEN=bearer_token_abc
DB_PASSWORD=secret123
```

**2. Reference in config**:
```yaml
headers:
  dev:
    X-API-Key: ${DEV_API_KEY}
    Authorization: ${AUTH_TOKEN}
  prod:
    X-API-Key: ${PROD_API_KEY}
    Authorization: ${AUTH_TOKEN}

variables:
  db_user: admin
  db_pass: ${DB_PASSWORD}
```

### Configuration Priority

Nodi merges configuration from multiple sources (highest to lowest priority):

1. **Inline headers** (`-H` flag in REPL)
2. **Session headers** (`set-header` command)
3. **Environment-specific headers** (config.yml `headers.dev`)
4. **Global headers** (config.yml `headers`)
5. **Default values**

---

## HTTP Requests

### Basic Requests

#### GET Requests

```bash
# Using alias
nodi> users

# Using full path
nodi> get /api/v1/users

# With path parameter
nodi> user:123

# With query parameters
nodi> users page=2 limit=10
```

#### POST Requests

```bash
# Inline JSON
nodi> post users {"name": "John", "email": "john@example.com"}

# Multi-line JSON (future feature)
nodi> post users <<EOF
{
  "name": "John",
  "email": "john@example.com",
  "address": {
    "city": "New York"
  }
}
EOF
```

#### PUT/PATCH Requests

```bash
# PUT (full update)
nodi> put user:123 {"name": "John Doe", "email": "john@example.com"}

# PATCH (partial update)
nodi> patch user:123 {"name": "John Doe"}
```

#### DELETE Requests

```bash
nodi> delete user:123
```

### HTTP Methods

Nodi supports all standard HTTP methods:

- `GET` - Retrieve resource
- `POST` - Create resource
- `PUT` - Update/replace resource
- `PATCH` - Partial update
- `DELETE` - Delete resource
- `HEAD` - Get headers only
- `OPTIONS` - Get supported methods

---

## Path Parameters

Path parameters allow dynamic URL segments.

### Configuration

Define aliases with parameter placeholders:

```yaml
services:
  myapi:
    dev:
      base_url: https://api.example.com
    aliases:
      # Single parameter
      user: /api/v1/users/{id}
      post: /api/v1/posts/{postId}

      # Multiple parameters (future)
      user_post: /api/v1/users/{userId}/posts/{postId}

      # Custom parameter names
      document: /api/v1/documents/{documentId}
      order: /api/v1/orders/{orderId}
```

### Usage

Use colon (`:`) syntax to provide parameter values:

```bash
# Basic usage
nodi> user:123              # GET /api/v1/users/123
nodi> post:456              # GET /api/v1/posts/456

# With any alphanumeric value
nodi> user:abc-123          # GET /api/v1/users/abc-123
nodi> document:doc_2024_01  # GET /api/v1/documents/doc_2024_01
```

### Parameter Auto-Detection

Nodi automatically detects parameter names from the alias:

```yaml
aliases:
  user: /users/{id}          # Uses 'id'
  order: /orders/{orderId}   # Uses 'orderId'
  doc: /docs/{documentId}    # Uses 'documentId'
```

You don't need to specify the parameter name - just provide the value:

```bash
nodi> order:ORD-12345       # Correctly substitutes orderId
```

### Combining with Query Parameters

```bash
# Path + query parameters
nodi> user:123 include=posts,comments
# GET /api/v1/users/123?include=posts,comments
```

### Combining with Filters

```bash
# Path parameter + filter
nodi> user:123 | .email
# GET /api/v1/users/123, then extract email

# Path parameter + predefined filter
nodi> user:123 | @summary
```

---

## Query Parameters

Query parameters append to the URL as key-value pairs.

### Basic Syntax

```bash
# Single parameter
nodi> users page=2

# Multiple parameters (space-separated)
nodi> users page=2 limit=10 sort=name

# With special characters
nodi> search q="john doe" status=active

# URL encoding handled automatically
nodi> search filter="name contains 'test'"
```

### Parameter Types

#### String Parameters

```bash
nodi> users name=john email=john@example.com
# GET /users?name=john&email=john@example.com
```

#### Numeric Parameters

```bash
nodi> posts page=2 limit=10 user_id=123
# GET /posts?page=2&limit=10&user_id=123
```

#### Boolean Parameters

```bash
nodi> users active=true verified=false
# GET /users?active=true&verified=false
```

#### Array Parameters

```bash
# Multiple values for same key
nodi> users ids=1,2,3
# Or (if supported by API)
nodi> users ids[]=1&ids[]=2&ids[]=3
```

### Special Characters

Nodi handles URL encoding automatically:

```bash
# Spaces
nodi> search q="hello world"
# GET /search?q=hello%20world

# Special characters
nodi> filter text="value & more"
# GET /filter?text=value%20%26%20more
```

### Combining Features

```bash
# Query params + path params
nodi> user:123 include=posts,comments
# GET /users/123?include=posts,comments

# Query params + filters
nodi> users page=1 limit=5 | @emails
# GET /users?page=1&limit=5, then filter emails

# All together
nodi> user:123 include=posts | @summary
# GET /users/123?include=posts, then apply summary
```

### Common Patterns

#### Pagination

```bash
# Page-based
nodi> users page=2 limit=20

# Offset-based
nodi> users offset=40 limit=20

# Cursor-based
nodi> users cursor=eyJpZCI6MTIzfQ
```

#### Sorting

```bash
# Single field
nodi> users sort=name

# Multiple fields
nodi> users sort=name,email

# With direction
nodi> users sort=-created_at    # Descending
nodi> users sort=+name           # Ascending
```

#### Filtering

```bash
# Simple filters
nodi> users status=active role=admin

# Complex filters
nodi> users filter="age > 25 AND status = 'active'"

# Date ranges
nodi> orders from=2024-01-01 to=2024-12-31
```

#### Field Selection

```bash
# Select specific fields
nodi> users fields=id,name,email

# Exclude fields
nodi> users exclude=password,secret_key
```

---

## Headers

Headers customize HTTP requests with authentication, content types, and custom metadata.

### Global Headers (Config)

Define headers in config for all requests in an environment:

```yaml
headers:
  dev:
    X-API-Key: ${DEV_API_KEY}
    Content-Type: application/json
    User-Agent: Nodi/1.0
  prod:
    X-API-Key: ${PROD_API_KEY}
    Content-Type: application/json
```

### Session Headers (REPL)

Set headers for the current REPL session:

```bash
# Set header
nodi> set-header X-Request-ID abc-123

# View all headers
nodi> headers

# Remove header
nodi> unset-header X-Request-ID
```

### Inline Headers (Per-Request)

Override headers for a single request:

```bash
# Single header
nodi> get users -H "X-Custom-Header: value"

# Multiple headers
nodi> get users -H "X-Custom: value1" -H "X-Another: value2"

# With variables
nodi> get users -H Cookie:$session_cookie

# Override existing header
nodi> get users -H Authorization:Bearer_$admin_token
```

### Header Variable Substitution

#### Config Variables in Headers

```yaml
# config.yml
variables:
  auth_token: "bearer_abc123"
  api_key: "key_xyz789"
  user1_cookie: "session_id=user1"
  user2_cookie: "session_id=user2"

headers:
  dev:
    Authorization: ${var:auth_token}
    X-API-Key: ${var:api_key}
    Cookie: ${var:user1_cookie}
```

#### Inline Variable Substitution

```bash
# Short form
nodi> get users -H Cookie:$user2_cookie

# Explicit form
nodi> get users -H Cookie:${user2_cookie}

# Compound values
nodi> get users -H Authorization:Bearer_$token

# Multiple variables
nodi> get profile -H Cookie:$cookie -H X-User-ID:$user_id
```

### Common Header Patterns

#### Authentication

```bash
# Bearer token
nodi> get /api/protected -H Authorization:Bearer_$token

# API Key
nodi> get /api/data -H X-API-Key:$api_key

# Basic Auth (base64 encoded)
nodi> get /api/secure -H Authorization:Basic_$base64_creds

# Cookie-based
nodi> get /api/profile -H Cookie:$session_cookie
```

#### Content Negotiation

```bash
# Request JSON
nodi> get /api/users -H Accept:application/json

# Request XML
nodi> get /api/users -H Accept:application/xml

# Request specific version
nodi> get /api/users -H Accept:application/vnd.api+json;version=2
```

#### Custom Headers

```bash
# Request ID for tracing
nodi> get /api/data -H X-Request-ID:$request_id

# Client information
nodi> get /api/data -H X-Client-Version:1.2.3

# Feature flags
nodi> get /api/feature -H X-Enable-Beta:true
```

### Header Priority

When the same header is defined in multiple places:

1. **Inline headers** (`-H` flag) - Highest priority
2. **Session headers** (`set-header`)
3. **Environment headers** (config `headers.dev`)
4. **Global headers** (config `headers`)

Example:
```yaml
# config.yml
headers:
  dev:
    Cookie: ${var:default_cookie}
```

```bash
# This overrides the config cookie
nodi> get profile -H Cookie:$admin_cookie
```

---

## Variables

Variables store reusable values for headers, scripts, and filters.

### Config Variables

Define variables in `config.yml`:

```yaml
variables:
  # Authentication
  dev_token: "dev_bearer_token_123"
  prod_token: "prod_bearer_token_456"

  # User sessions
  user1_cookie: "session_id=user1_abc"
  user2_cookie: "session_id=user2_xyz"
  admin_cookie: "session_id=admin_000"

  # API keys
  api_key: "${API_KEY}"  # From environment

  # Test data
  test_user_id: "123"
  test_email: "test@example.com"
```

### Using Variables

#### In Headers

```yaml
# Config
headers:
  dev:
    Authorization: Bearer ${var:dev_token}
    Cookie: ${var:user1_cookie}
```

#### Inline (REPL)

```bash
# In headers
nodi> get users -H Cookie:$user1_cookie

# Variable substitution
nodi> get user:$test_user_id
```

### Session Variables

Manage variables during REPL session:

```bash
# View all variables
nodi> variables

# Get specific variable
nodi> get-variable test_user_id

# Set/update variable
nodi> set-variable test_user_id 456
```

### Script Variables

Variables in scripts have isolated scope:

```nodi
# test_script.nodi
$user_id = 123
$name = "John"

GET user:$user_id
$user = $data

assert $user.id == $user_id
print $user.name
```

**Key Points**:
- Script variables don't persist after execution
- Use `$variable` syntax
- Access nested properties: `$user.email`
- Named parameters become variables

### Variable Syntax

| Syntax | Context | Example |
|--------|---------|---------|
| `${var:name}` | Config headers | `Authorization: ${var:token}` |
| `${ENV_VAR}` | Environment vars | `API_Key: ${API_KEY}` |
| `$variable` | Scripts, inline | `-H Cookie:$session` |
| `${variable}` | Explicit form | `-H Cookie:${session}` |
| `$var.field` | Property access | `$user.email` |

### Best Practices

**✅ Do**:
- Use descriptive names: `user1_session`, not `s1`
- Store test credentials in variables
- Use environment variables for secrets
- Check available variables with `variables` command

**❌ Don't**:
- Commit real credentials to config files
- Use overly generic names: `var1`, `temp`
- Store sensitive data in plain text

---

## Filters

Filters extract and transform JSON response data using jq syntax.

### Basic Filter Syntax

```bash
# Get specific field
nodi> user:1 | .email
"alice@example.com"

# Extract from array
nodi> users | .[*].email
["alice@example.com", "bob@example.com"]

# Count items
nodi> users | length
100

# First item
nodi> users | .[0]
{"id": 1, "name": "Alice"}
```

### Predefined Filters

Define reusable filters in config:

```yaml
filters:
  # Extract emails from array
  emails: ".[*].email"

  # Extract IDs
  ids: ".[*].id"

  # Count items
  count: "length"

  # First item
  first: ".[0]"

  # Get names
  names: ".[*].name"

  # Filter active users
  active_users: ".[] | select(.active == true)"
```

**Usage**:
```bash
nodi> users | @emails
["alice@example.com", "bob@example.com"]

nodi> posts | @count
100

nodi> users | @first
{"id": 1, "name": "Alice"}
```

### jq Filter Examples

#### Field Extraction

```bash
# Single field
nodi> user:1 | .name
"Alice"

# Multiple fields
nodi> user:1 | {name, email}
{"name": "Alice", "email": "alice@example.com"}

# Nested fields
nodi> user:1 | .address.city
"New York"
```

#### Array Operations

```bash
# Get all items
nodi> users | .[]

# Map fields from array
nodi> users | .[*].name
["Alice", "Bob", "Charlie"]

# Filter array
nodi> users | .[] | select(.active == true)

# Sort array
nodi> users | sort_by(.name)

# Limit results
nodi> users | .[0:5]  # First 5
```

#### Conditionals

```bash
# Select with condition
nodi> users | .[] | select(.age > 25)

# Multiple conditions
nodi> users | .[] | select(.age > 25 and .active == true)

# Contains
nodi> users | .[] | select(.name | contains("Alice"))
```

#### Aggregation

```bash
# Count
nodi> users | length

# Sum
nodi> orders | .[*].total | add

# Average (future jq version)
nodi> orders | .[*].total | add / length

# Min/Max
nodi> orders | .[*].total | min
nodi> orders | .[*].total | max
```

#### Transformation

```bash
# Add field
nodi> users | .[*] | . + {processed: true}

# Rename field
nodi> users | .[*] | {id, username: .name, email}

# Group by (advanced)
nodi> users | group_by(.department)
```

### Filter Chaining

Combine multiple filters:

```bash
# Extract, filter, then count
nodi> users | .[*] | select(.active == true) | length

# Get active users' emails
nodi> users | .[] | select(.active == true) | .email

# Predefined + inline
nodi> users | @active_users | .[*].email
```

### Common Filter Patterns

```bash
# Get array length
| length

# Get first item
| .[0]

# Get last item
| .[-1]

# Extract single field from array
| .[*].fieldname

# Filter by value
| .[] | select(.field == "value")

# Check if empty
| length == 0

# Extract nested field
| .parent.child.field

# Convert to array of single field
| [.[].fieldname]
```

---

## Projections

Projections reduce JSON output by selecting specific fields.

### Predefined Projections

Define field selections in config:

```yaml
projections:
  # User summary
  user_summary:
    - id
    - name
    - email

  # Post summary
  post_summary:
    - id
    - title
    - userId

  # Order essentials
  order_essentials:
    - orderId
    - total
    - status
    - created_at
```

### Usage

```bash
# Apply projection
nodi> users | %user_summary
[
  {"id": 1, "name": "Alice", "email": "alice@example.com"},
  {"id": 2, "name": "Bob", "email": "bob@example.com"}
]

# Single item
nodi> user:1 | %user_summary
{"id": 1, "name": "Alice", "email": "alice@example.com"}
```

### Combining with Filters

```bash
# Projection then filter
nodi> users | %user_summary | @emails
["alice@example.com", "bob@example.com"]

# Filter then projection
nodi> users | @active_users | %user_summary
```

### Nested Projections

```yaml
projections:
  user_with_address:
    - id
    - name
    - address:
        - city
        - country
```

### Benefits

- **Reduce payload size**: Only transfer needed fields
- **Improve readability**: Focus on relevant data
- **Faster responses**: Less data to process
- **Reusable**: Define once, use everywhere

---

## Scripting

Automate API testing with Python-like scripts.

### Script Basics

Create `.nodi` files with Python-like syntax:

```nodi
# test_users.nodi
echo "Testing users API..."

# Get all users
GET users | @count
$count = $data
assert $count > 0

echo "Found users"
print $count

# Get first user
GET user:1
$user = $data
assert $user.id == 1
assert $user.email != null

echo "Tests passed!"
```

### Script Syntax

#### Comments

```nodi
# This is a comment
```

#### Variables

```nodi
# Assignment
$user_id = 123
$name = "John"
$active = true

# From response
GET users
$users = $data

# Nested access
$email = $user.email
$first = $data.0
```

#### HTTP Requests

```nodi
# Basic requests
GET users
POST users {"name": "John"}
PUT user:123 {"name": "John Doe"}
DELETE user:123

# With filters
GET users | @emails
GET users | %user_summary

# With variables
GET user:$user_id
```

#### Assertions

```nodi
# Comparisons
assert $status == 200
assert $count > 0
assert $count >= 10
assert $name != null

# Membership
assert "john" in $email
assert "error" not in $message
```

#### Output

```nodi
# Echo message
echo "Starting test..."
echo "User ID: $user_id"

# Print variable
print $count
print $user.email

# Print object (formatted JSON)
print $users
```

### Named Parameters

Scripts accept parameters:

```nodi
# test_user.nodi
echo "Testing user: $user_id"

GET user:$user_id
assert $data.id == $user_id

print $data.name
```

**Run with parameters**:
```bash
nodi> run test_user.nodi user_id=123
```

### Running Scripts

#### Single Script

```bash
# Run script
nodi> run test_users.nodi

# With parameters
nodi> run test_user.nodi user_id=123 env=dev

# Show script
nodi> show test_users.nodi
```

#### Multiple Scripts Sequential

```bash
# Run multiple scripts in order
nodi> run test1.nodi test2.nodi test3.nodi

# With glob pattern
nodi> run test_*.nodi
```

#### Multiple Scripts Parallel

```bash
# Run scripts concurrently
nodi> run --parallel test1.nodi test2.nodi test3.nodi

# Parallel with pattern
nodi> run --parallel load_test_*.nodi
```

### Test Suites

Create YAML files to orchestrate scripts:

#### Simple Sequential Suite

```yaml
# integration_suite.yml
name: Integration Tests
scripts:
  - setup.nodi
  - test_users.nodi
  - test_posts.nodi
  - cleanup.nodi

options:
  stop_on_error: true
```

#### Parallel Groups

```yaml
# parallel_suite.yml
name: Parallel Load Test
parallel_groups:
  - name: User APIs
    parallel: true
    scripts:
      - test_user_get.nodi
      - test_user_create.nodi
      - test_user_update.nodi

  - name: Post APIs
    parallel: true
    scripts:
      - test_post_list.nodi
      - test_post_create.nodi
```

#### Mixed Sequential & Parallel

```yaml
# mixed_suite.yml
name: Complete Test Suite
steps:
  - name: Setup
    script: setup.nodi

  - name: Parallel Tests
    parallel: true
    scripts:
      - test_users.nodi
      - test_posts.nodi

  - name: Sequential Flow
    parallel: false
    scripts:
      - test_order_create.nodi
      - test_order_payment.nodi

  - name: Cleanup
    script: cleanup.nodi
```

**Run suite**:
```bash
nodi> run-suite integration_suite.yml
```

### Script Organization

Organize scripts by feature:

```
~/.nodi/scripts/
├── auth/
│   ├── test_login.nodi
│   ├── test_logout.nodi
│   └── test_refresh.nodi
├── users/
│   ├── test_create_user.nodi
│   ├── test_update_user.nodi
│   └── test_delete_user.nodi
└── suites/
    ├── smoke_tests.yml
    └── integration_tests.yml
```

### Special Variables

- `$response` - Full HTTP response object
- `$data` - Response data (shortcut for `$response.data`)
- Parameters become variables (`user_id=123` → `$user_id`)

### Best Practices

**✅ Do**:
- Add echo messages for progress
- Use descriptive variable names
- Assert early and often
- Use projections to reduce data
- Organize scripts by feature
- Use test suites for complex workflows

**❌ Don't**:
- Create overly long scripts
- Skip assertions
- Hardcode values (use parameters)
- Ignore script output

---

## SSL/TLS Certificates

Nodi supports SSL/TLS certificates for secure API communication.

### Basic SSL Configuration

#### Disable SSL Verification (Development Only)

```yaml
services:
  myapi:
    dev:
      base_url: https://localhost:8000
      verify_ssl: false  # Only for development!
```

⚠️ **Warning**: Never disable SSL verification in production!

#### Enable SSL Verification

```yaml
services:
  myapi:
    prod:
      base_url: https://api.example.com
      verify_ssl: true  # Default
```

### Client Certificates

For mutual TLS (mTLS) authentication:

```yaml
certificates:
  cert_file: /path/to/client-cert.pem
  key_file: /path/to/client-key.pem
  ca_bundle: /path/to/ca-bundle.crt
```

#### Per-Service Certificates

```yaml
services:
  secure-api:
    prod:
      base_url: https://secure.example.com
      certificates:
        cert_file: /path/to/service-cert.pem
        key_file: /path/to/service-key.pem
```

### Custom CA Bundle

For self-signed certificates or custom CA:

```yaml
certificates:
  ca_bundle: /path/to/custom-ca-bundle.crt
```

Or per-service:

```yaml
services:
  internal-api:
    dev:
      base_url: https://internal.company.com
      ca_bundle: /path/to/company-ca.crt
```

### Certificate Formats

Nodi supports standard certificate formats:

- **PEM**: Most common format (`.pem`, `.crt`, `.cer`)
- **DER**: Binary format (convert to PEM first)
- **PKCS#12**: Password-protected bundles (`.p12`, `.pfx`)

#### Convert Certificates

```bash
# DER to PEM
openssl x509 -inform der -in cert.der -out cert.pem

# PKCS#12 to PEM
openssl pkcs12 -in cert.p12 -out cert.pem -nodes
```

### Troubleshooting Certificates

#### SSL Certificate Verification Failed

```bash
# Error
SSL: CERTIFICATE_VERIFY_FAILED

# Solution 1: Add custom CA bundle
certificates:
  ca_bundle: /path/to/ca-bundle.crt

# Solution 2: Disable verification (dev only)
verify_ssl: false
```

#### Certificate File Not Found

```bash
# Error
FileNotFoundError: cert_file not found

# Solution: Use absolute paths
certificates:
  cert_file: /Users/username/certs/client.pem
  key_file: /Users/username/certs/client-key.pem
```

#### Certificate Expired

```bash
# Check expiration
openssl x509 -in cert.pem -noout -dates

# Renew certificate or get new one
```

---

# Reference

## Configuration Reference

### Complete Configuration Example

```yaml
# ~/.nodi/config.yml

# Service definitions
services:
  # Service 1
  my-api:
    # Environment 1
    dev:
      base_url: http://localhost:3000
      verify_ssl: false
      timeout: 30
      http2: false
    # Environment 2
    prod:
      base_url: https://api.myapp.com
      verify_ssl: true
      timeout: 60
      certificates:
        cert_file: /path/to/cert.pem
        key_file: /path/to/key.pem
    # Aliases (shared across environments)
    aliases:
      users: /api/v1/users
      user: /api/v1/users/{id}
      posts: /api/v1/posts
      post: /api/v1/posts/{postId}

  # Service 2
  external-api:
    prod:
      base_url: https://partner-api.com
    aliases:
      orders: /v2/orders
      order: /v2/orders/{orderId}

# Global headers
headers:
  dev:
    X-API-Key: ${DEV_API_KEY}
    Content-Type: application/json
  prod:
    X-API-Key: ${PROD_API_KEY}
    Content-Type: application/json

# Variables
variables:
  test_user_id: "123"
  admin_token: "${ADMIN_TOKEN}"
  user1_cookie: "session_id=user1"
  user2_cookie: "session_id=user2"

# Predefined filters
filters:
  emails: ".[*].email"
  ids: ".[*].id"
  count: "length"
  first: ".[0]"
  active: ".[] | select(.active == true)"

# Predefined projections
projections:
  user_summary:
    - id
    - name
    - email
  post_summary:
    - id
    - title
    - userId

# Defaults
default_service: my-api
default_environment: dev

# Global certificates
certificates:
  ca_bundle: /path/to/ca-bundle.crt
```

### Service Configuration Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `base_url` | string | Required | Base URL for the service |
| `verify_ssl` | boolean | true | Verify SSL certificates |
| `timeout` | integer | 30 | Request timeout in seconds |
| `http2` | boolean | false | Enable HTTP/2 |
| `follow_redirects` | boolean | true | Follow HTTP redirects |
| `certificates.cert_file` | string | None | Client certificate file |
| `certificates.key_file` | string | None | Client key file |
| `ca_bundle` | string | None | Custom CA bundle |

---

## Syntax Reference

### REPL Syntax

```
# Service/Environment
use <service>.<env>
service <name>
env <name>

# HTTP Requests
<method> <endpoint> [json] [-H header]
<alias>
<alias>:<param>
<alias> <query_params>
<alias> | <filter>

# Headers
-H "Name: Value"
-H Name:Value
-H Name:$variable

# Variables
$variable
${variable}
${var:name}
$variable.field

# Filters
| .field
| .[*].field
| @filter_name
| %projection_name

# Query Parameters
key=value
key1=value1 key2=value2

# Commands
help, exit, clear
services, envs
headers, variables
history
scripts, show, run
format <json|yaml|table>
```

### Script Syntax

```nodi
# Comments
# This is a comment

# Variables
$var = value
$var = $other_var
$var = $obj.field

# HTTP Requests
GET endpoint
POST endpoint json
PUT endpoint:param json
DELETE endpoint

# With filters
GET endpoint | @filter
GET endpoint | %projection

# Assertions
assert $var == value
assert $var > 0
assert $var != null
assert value in $var

# Output
echo "message"
echo "value: $var"
print $variable
```

---

## Filter Reference

### Basic Filters

```bash
# Identity
| .

# Field access
| .fieldname
| .parent.child

# Array index
| .[0]        # First item
| .[-1]       # Last item
| .[2:5]      # Slice (index 2-4)

# Array iteration
| .[]         # All items
| .[*]        # All items (map)

# Extract from array
| .[*].field
```

### Operators

```bash
# Comparison
| select(. == value)
| select(. != value)
| select(. > value)
| select(. < value)
| select(. >= value)
| select(. <= value)

# Logical
| select(. > 10 and . < 20)
| select(. < 0 or . > 100)
| select(. | not)

# String operations
| select(. | contains("text"))
| select(. | startswith("prefix"))
| select(. | endswith("suffix"))
```

### Functions

```bash
# Array functions
| length
| reverse
| sort
| sort_by(.field)
| unique
| min
| max
| add (sum)
| first
| last

# String functions
| tostring
| tonumber
| split("delimiter")
| join("separator")

# Type checks
| type
| isnumber
| isstring
| isarray
| isobject

# Object functions
| keys
| values
| has("field")
| to_entries
| from_entries
```

### Complex Filters

```bash
# Map
| .[*] | .field

# Select with condition
| .[] | select(.age > 25)

# Multiple conditions
| .[] | select(.age > 25 and .active == true)

# Transformation
| .[*] | {id, name, email}

# Group by (requires jq 1.6+)
| group_by(.category)

# Conditional
| if .status == "active" then .name else "N/A" end
```

---

## Troubleshooting

### Installation Issues

#### Import Errors

**Problem**: `ModuleNotFoundError: No module named 'nodi'`

**Solution**:
```bash
pip install -e .
# Or with full dependencies
pip install -e .[full]
```

#### Missing Dependencies

**Problem**: `ImportError: cannot import name 'jq'`

**Solution**:
```bash
pip install -r requirements-jq.txt
# Or
pip install jq
```

### Configuration Issues

#### Config Not Found

**Problem**: `FileNotFoundError: config.yml not found`

**Solution**:
```bash
nodi init
# Edit ~/.nodi/config.yml
```

#### Invalid Configuration

**Problem**: `ConfigError: Invalid configuration`

**Solution**:
```bash
nodi validate
# Check error messages and fix config
```

#### Service Not Found

**Problem**: `Service 'xyz' not found in configuration`

**Solution**:
```bash
# List available services
nodi services

# Check config.yml has the service defined
cat ~/.nodi/config.yml
```

### Request Issues

#### Connection Errors

**Problem**: `ConnectionError: Failed to connect`

**Solutions**:
1. Check base URL is correct
2. Verify service is running
3. Check network connectivity
4. Try with curl to verify endpoint

```bash
curl https://api.example.com/health
```

#### Timeout Errors

**Problem**: `TimeoutError: Request timed out`

**Solution**:
```yaml
# Increase timeout in config
services:
  myapi:
    dev:
      timeout: 60  # seconds
```

#### SSL Errors

**Problem**: `SSL: CERTIFICATE_VERIFY_FAILED`

**Solutions**:

1. **Add CA bundle** (recommended):
```yaml
certificates:
  ca_bundle: /path/to/ca-bundle.crt
```

2. **Disable verification** (dev only):
```yaml
services:
  myapi:
    dev:
      verify_ssl: false
```

3. **Check certificate expiration**:
```bash
openssl s_client -connect api.example.com:443 -showcerts
```

#### 401/403 Errors

**Problem**: `401 Unauthorized` or `403 Forbidden`

**Solutions**:
1. Check authentication headers
2. Verify API keys/tokens are correct
3. Check token hasn't expired
4. Use inline headers to test different credentials

```bash
# Check current headers
nodi> headers

# Test with different token
nodi> get /api/protected -H Authorization:Bearer_$new_token
```

### Scripting Issues

#### Script Not Found

**Problem**: `Script file not found: test.nodi`

**Solution**:
- Ensure script is in current directory or `~/.nodi/scripts/`
- Use absolute path if needed
- Check file extension is `.nodi`

```bash
# List scripts
nodi> scripts

# Use absolute path
nodi> run /path/to/script.nodi
```

#### Assertion Failed

**Problem**: `Assertion failed at line 10: $status == 200`

**Solution**:
- Add `print $status` before assertion to see actual value
- Check API response
- Verify endpoint is correct

```nodi
# Debug assertion
GET users
print $response.status_code  # Debug
assert $response.status_code == 200
```

#### Variable Not Found

**Problem**: `Variable not defined: $user_id`

**Solutions**:
1. Pass as parameter:
```bash
nodi> run script.nodi user_id=123
```

2. Define in script:
```nodi
$user_id = 123
GET user:$user_id
```

### Filter Issues

#### Invalid Filter Expression

**Problem**: `FilterError: Invalid jq expression`

**Solution**:
- Test filter with simple data first
- Check jq syntax
- Use predefined filters for complex expressions

```bash
# Test filter incrementally
nodi> users | length       # Works?
nodi> users | .[*]         # Works?
nodi> users | .[*].email   # Works?
```

#### Predefined Filter Not Found

**Problem**: `Unknown filter: @emails`

**Solution**:
```bash
# List available filters
nodi> filters

# Check config.yml has the filter defined
filters:
  emails: ".[*].email"
```

### Environment Issues

#### Variable Substitution Not Working

**Problem**: Headers show literal `${VAR}` instead of value

**Solutions**:
1. Check `.env` file exists
2. Verify variable name matches exactly
3. Check environment variable is set

```bash
# Check environment variables
echo $API_KEY

# Check Nodi variables
nodi> variables
```

### Performance Issues

#### Slow Responses

**Solutions**:
1. Use projections to reduce data
2. Add query parameters to limit results
3. Use pagination
4. Enable HTTP/2

```yaml
services:
  myapi:
    prod:
      http2: true
```

```bash
# Reduce data with projection
nodi> users | %user_summary

# Limit results
nodi> users limit=10
```

#### Memory Issues with Large Responses

**Solutions**:
1. Use streaming (future feature)
2. Paginate requests
3. Use filters to reduce data

```bash
# Instead of
nodi> users  # Gets all 10,000 users

# Do
nodi> users page=1 limit=100
```

### Common Error Messages

| Error | Cause | Solution |
|-------|-------|----------|
| `Config not found` | No config.yml | Run `nodi init` |
| `Service not found` | Invalid service name | Run `nodi services` |
| `SSL verify failed` | Certificate issue | Add CA bundle or disable verification (dev only) |
| `Connection refused` | Service not running | Start service or check URL |
| `Timeout` | Request taking too long | Increase timeout in config |
| `401 Unauthorized` | Missing/invalid auth | Check headers and credentials |
| `404 Not Found` | Invalid endpoint | Verify endpoint path |
| `Script not found` | Invalid script path | Check script location |
| `Assertion failed` | Test condition not met | Debug with print statements |
| `Filter error` | Invalid jq syntax | Test filter incrementally |

### Getting Help

1. **Check this documentation** - Most issues are covered here
2. **Run `nodi validate`** - Validates your configuration
3. **Use `nodi --help`** - Shows CLI help
4. **Type `help` in REPL** - Shows REPL commands
5. **Check logs** - Enable verbose logging if available
6. **GitHub Issues** - Report bugs or request help

---

**Documentation Complete!** For quick reference, see [QUICKSTART.md](QUICKSTART.md). To extend Nodi, see [DEVELOPMENT.md](DEVELOPMENT.md).
