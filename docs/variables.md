# Variable Substitution in Nodi

## Overview

Nodi supports variable substitution in configuration files, allowing you to inject dynamic values into headers during REST API calls. This is particularly useful for managing authentication cookies, tokens, and other values that differ between users or sessions.

## Syntax

Variables are defined in the `variables` section of your config.yml and referenced using the `${var:variable_name}` syntax in headers.

## Configuration

### Defining Variables

Add a `variables` section to your config.yml:

```yaml
variables:
  auth_cookie: "session_id=abc123; user_id=user1"
  api_token: "your_api_token_here"
  tenant_id: "tenant-456"
```

### Using Variables in Headers

Reference variables in your headers using `${var:variable_name}`:

```yaml
headers:
  dev:
    X-Environment: development
    Cookie: ${var:auth_cookie}
    Authorization: Bearer ${var:api_token}
    X-Tenant-ID: ${var:tenant_id}

  qa:
    X-Environment: qa
    Cookie: ${var:auth_cookie}
    Authorization: Bearer ${var:api_token}

  prod:
    X-Environment: production
    Cookie: ${var:auth_cookie}
    Authorization: Bearer ${var:api_token}
```

### Service-Specific Headers

You can also use variables in service-specific headers:

```yaml
services:
  user-service:
    dev:
      base_url: https://user-service.dev.company.com
      headers:
        Cookie: ${var:auth_cookie}
        X-Custom-Header: ${var:custom_value}
```

## Runtime Usage

### Updating Variables Programmatically

Variables can be updated at runtime, which makes them ideal for switching between different user sessions:

```python
from nodi.config.loader import ConfigLoader
from nodi.environment.headers import HeaderManager

# Load config
loader = ConfigLoader()
config = loader.load()

# Create header manager
header_manager = HeaderManager(config)

# Update a variable for a different user
header_manager.set_variable('auth_cookie', 'session_id=xyz789; user_id=user2')

# Get headers with the updated variable
headers = header_manager.get_headers('user-service', 'dev')
# Cookie header will now contain: session_id=xyz789; user_id=user2
```

### Getting Variable Values

```python
# Get a single variable
value = header_manager.get_variable('auth_cookie')

# Get all variables
all_vars = header_manager.list_variables()
```

## Use Cases

### 1. Different Auth Cookies for Different Users

```yaml
variables:
  auth_cookie: "session_id=default"

headers:
  dev:
    Cookie: ${var:auth_cookie}
```

Then update at runtime:
```python
# Switch to user 1
header_manager.set_variable('auth_cookie', 'session_id=user1_session; user_id=user1')

# Switch to user 2
header_manager.set_variable('auth_cookie', 'session_id=user2_session; user_id=user2')
```

### 2. Per-Environment Tokens

```yaml
variables:
  dev_token: "dev_jwt_token"
  qa_token: "qa_jwt_token"
  prod_token: "prod_jwt_token"

headers:
  dev:
    Authorization: Bearer ${var:dev_token}
  qa:
    Authorization: Bearer ${var:qa_token}
  prod:
    Authorization: Bearer ${var:prod_token}
```

### 3. Dynamic Correlation IDs

```yaml
variables:
  correlation_id: "initial-correlation-id"

headers:
  dev:
    X-Correlation-ID: ${var:correlation_id}
```

Update per request:
```python
import uuid

# Generate a new correlation ID for each request
header_manager.set_variable('correlation_id', str(uuid.uuid4()))
```

## Variable Types

### 1. Custom Variables (${var:name})

These are defined in the `variables` section and resolved at request time. They can be updated dynamically during runtime.

```yaml
variables:
  auth_cookie: "value"

headers:
  dev:
    Cookie: ${var:auth_cookie}  # Resolved at request time
```

### 2. Environment Variables (${ENV_VAR})

These reference system environment variables and are resolved at config load time.

```yaml
headers:
  dev:
    X-API-Key: ${DEV_API_KEY}  # Resolved from environment variable
```

## Differences Between Variable Types

| Feature | Custom Variables (`${var:name}`) | Environment Variables (`${ENV_VAR}`) |
|---------|----------------------------------|-------------------------------------|
| When resolved | Request time | Config load time |
| Can be updated at runtime | Yes | No |
| Source | `variables` section in config | System environment variables |
| Use case | Dynamic auth cookies, session tokens | API keys, static configuration |

## Complete Example

```yaml
services:
  api-service:
    dev:
      base_url: https://api.dev.example.com
    qa:
      base_url: https://api.qa.example.com
    prod:
      base_url: https://api.prod.example.com

    aliases:
      users: /api/v1/users
      user: /api/v1/users/{id}

headers:
  dev:
    X-API-Key: ${DEV_API_KEY}        # Environment variable (static)
    X-Environment: development
    Cookie: ${var:auth_cookie}       # Custom variable (dynamic)
    Authorization: Bearer ${var:dev_token}

  qa:
    X-API-Key: ${QA_API_KEY}
    X-Environment: qa
    Cookie: ${var:auth_cookie}
    Authorization: Bearer ${var:qa_token}

  prod:
    X-API-Key: ${PROD_API_KEY}
    X-Environment: production
    Cookie: ${var:auth_cookie}
    Authorization: Bearer ${var:prod_token}

default_environment: dev
default_service: api-service

variables:
  # These can be updated at runtime
  auth_cookie: "session_id=default_session"
  dev_token: "dev_jwt_token_here"
  qa_token: "qa_jwt_token_here"
  prod_token: "prod_jwt_token_here"
```

## Best Practices

1. **Use custom variables for dynamic values**: Auth cookies, session tokens, and values that change frequently should use `${var:name}` syntax.

2. **Use environment variables for static config**: API keys and other values that are set once per environment should use `${ENV_VAR}` syntax.

3. **Set default values**: Always provide default values in the `variables` section to prevent errors.

4. **Secure sensitive data**: Don't commit actual auth cookies or tokens to version control. Use placeholder values in the config file.

5. **Update variables before requests**: When switching users or sessions, update the relevant variables before making API calls.

## Security Considerations

- Variables are stored in memory and are visible in the Config object
- Sensitive values like auth cookies are masked in header display (via `mask_sensitive_headers()`)
- Never commit actual production credentials to configuration files
- Use environment variables for long-term credentials
- Use custom variables for short-lived session data
