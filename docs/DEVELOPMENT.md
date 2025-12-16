# Nodi Development Guide

Guide for extending Nodi with custom providers and scripting functionality.

## Table of Contents

### Getting Started
- [Development Setup](#development-setup)
- [Project Structure](#project-structure)
- [Architecture Overview](#architecture-overview)

### Extending Nodi
- [Custom Providers](#custom-providers)
- [Scripting System](#scripting-system)
- [Adding Features](#adding-features)

### Contributing
- [Development Workflow](#development-workflow)
- [Testing Guidelines](#testing-guidelines)
- [Code Quality](#code-quality)

---

# Development Setup

## Prerequisites

- Python 3.8 or higher
- pip
- virtualenv (recommended)
- Git

## Setup Steps

```bash
# Clone repository
git clone https://github.com/yourusername/nodi.git
cd nodi

# Create virtual environment
python -m venv .venv

# Activate virtual environment
# On Windows:
.venv\Scripts\activate
# On Unix/macOS:
source .venv/bin/activate

# Install in development mode with all dependencies
pip install -e .[dev,full]
```

## Verify Installation

```bash
# Check version
nodi --version

# Run tests
pytest

# Start REPL
nodi repl
```

---

# Project Structure

```
nodi/
├── nodi/                      # Main package
│   ├── __init__.py           # Package initialization
│   ├── __main__.py           # Entry point
│   ├── cli.py                # CLI interface (Click)
│   ├── repl.py               # Interactive REPL
│   │
│   ├── config/               # Configuration management
│   │   ├── loader.py         # Config file loading & merging
│   │   ├── models.py         # Data models
│   │   └── validator.py      # Config validation
│   │
│   ├── environment/          # Service/environment management
│   │   ├── manager.py        # Context management
│   │   ├── resolver.py       # URL resolution
│   │   └── headers.py        # Header management
│   │
│   ├── providers/            # Data provider system
│   │   ├── base.py           # Base provider class
│   │   ├── manager.py        # Provider manager
│   │   ├── rest.py           # REST/HTTP provider
│   │   └── [custom]/         # Custom providers
│   │
│   ├── scripting/            # Scripting system
│   │   ├── parser.py         # Script parser
│   │   ├── engine.py         # Script execution engine
│   │   └── suite.py          # Test suite runner
│   │
│   ├── formatters/           # Output formatters
│   │   ├── json.py           # JSON formatter
│   │   ├── yaml_fmt.py       # YAML formatter
│   │   ├── table.py          # Table formatter
│   │   └── csv_fmt.py        # CSV formatter
│   │
│   ├── filters.py            # jq-style filtering
│   ├── projections.py        # Field projections
│   ├── history.py            # Request history
│   ├── certificates.py       # SSL/TLS management
│   │
│   └── utils/                # Utilities
│       ├── color.py          # Terminal colors
│       └── validators.py     # Validators
│
├── tests/                    # Test suite
├── examples/                 # Example configurations
├── docs/                     # Documentation
├── setup.py                  # Package setup
├── pyproject.toml            # Project metadata
└── requirements.txt          # Dependencies
```

---

# Architecture Overview

## Core Components

### 1. Configuration System

**Components**:
- `ConfigLoader`: Loads and merges configs from multiple sources
- `Config`/`Service`/`ServiceEnvironment`: Data models
- `ConfigValidator`: Validates configuration

**Flow**:
```
config.yml → ConfigLoader → Config model → EnvironmentManager
```

### 2. Environment Management

**Components**:
- `EnvironmentManager`: Manages current service/environment context
- `URLResolver`: Parses `service.env@endpoint` syntax
- `HeaderManager`: Manages HTTP headers

**Responsibilities**:
- Track current service/environment
- Resolve endpoints with parameters
- Manage session headers

### 3. Provider System

**Components**:
- `DataProvider`: Abstract base class for data sources
- `RestProvider`: HTTP/REST implementation
- `ProviderManager`: Manages provider instances

**Extensibility**:
Allows adding providers for:
- Databases (MongoDB, PostgreSQL, MySQL)
- Message queues (Kafka, RabbitMQ)
- Search engines (Elasticsearch)
- Caches (Redis, Memcached)
- Log systems (Splunk, CloudWatch)

### 4. Scripting System

**Components**:
- `ScriptParser`: Parses `.nodi` files into instructions
- `ScriptEngine`: Executes parsed scripts
- `SuiteRunner`: Orchestrates multiple scripts

**Features**:
- Python-like syntax
- Variable management
- HTTP request execution
- Assertions and validation
- Sequential and parallel execution

### 5. REPL Interface

**Built with**:
- `prompt_toolkit` - Interactive prompts
- Auto-completion
- History
- Syntax highlighting

**Commands**:
- Service/environment management
- HTTP requests
- Filters and projections
- Variables and headers
- Scripts

### 6. Formatters

Output formatters for different use cases:
- **JSON**: Pretty-printed with syntax highlighting
- **YAML**: Human-readable format
- **Table**: ASCII tables for structured data
- **CSV**: Export data for spreadsheets

---

# Custom Providers

## Provider Architecture

Providers allow Nodi to connect to different data sources beyond HTTP APIs.

### Base Provider Interface

All providers extend `DataProvider`:

```python
from nodi.providers.base import DataProvider, ProviderRequest, ProviderResponse

class DataProvider:
    """Base class for all data providers."""

    def __init__(self, name: str, config: Dict[str, Any]):
        self.name = name
        self.config = config

    def request(self, request: ProviderRequest) -> ProviderResponse:
        """Execute a request and return response."""
        raise NotImplementedError

    def test_connection(self) -> bool:
        """Test if connection is working."""
        raise NotImplementedError
```

### Request/Response Models

```python
@dataclass
class ProviderRequest:
    """Standard request format."""
    method: str  # GET, POST, QUERY, etc.
    resource: str  # Endpoint, collection, query
    params: Dict[str, Any]  # Query parameters
    body: Any  # Request body
    headers: Dict[str, str]  # Headers

@dataclass
class ProviderResponse:
    """Standard response format."""
    status_code: int  # HTTP status or equivalent
    data: Any  # Response data
    headers: Dict[str, str]  # Response headers
    duration: float  # Request duration in seconds
```

## Creating a Custom Provider

### Example: MongoDB Provider

```python
# nodi/providers/mongodb.py

from typing import Dict, Any
from pymongo import MongoClient
from nodi.providers.base import DataProvider, ProviderRequest, ProviderResponse

class MongoDBProvider(DataProvider):
    """MongoDB data provider."""

    def __init__(self, name: str = "mongodb", config: Dict[str, Any] = None):
        super().__init__(name, config)
        self.client = None
        self.db = None
        self._setup_connection()

    def _setup_connection(self):
        """Setup MongoDB connection."""
        connection_string = self.config.get("connection_string")
        database = self.config.get("database")

        self.client = MongoClient(connection_string)
        self.db = self.client[database]

    def request(self, request: ProviderRequest) -> ProviderResponse:
        """Execute MongoDB operation."""
        import time
        start_time = time.time()

        try:
            method = request.method.upper()
            collection_name = request.resource
            collection = self.db[collection_name]

            if method == "FIND":
                # Find documents
                query = request.params.get("query", {})
                limit = request.params.get("limit", 0)

                cursor = collection.find(query)
                if limit > 0:
                    cursor = cursor.limit(limit)

                data = list(cursor)
                status_code = 200

            elif method == "INSERT":
                # Insert document
                document = request.body
                result = collection.insert_one(document)
                data = {"inserted_id": str(result.inserted_id)}
                status_code = 201

            elif method == "UPDATE":
                # Update documents
                query = request.params.get("query", {})
                update = request.body
                result = collection.update_many(query, {"$set": update})
                data = {"modified_count": result.modified_count}
                status_code = 200

            elif method == "DELETE":
                # Delete documents
                query = request.params.get("query", {})
                result = collection.delete_many(query)
                data = {"deleted_count": result.deleted_count}
                status_code = 200

            else:
                raise ValueError(f"Unsupported method: {method}")

            duration = time.time() - start_time

            return ProviderResponse(
                status_code=status_code,
                data=data,
                headers={},
                duration=duration
            )

        except Exception as e:
            duration = time.time() - start_time
            return ProviderResponse(
                status_code=500,
                data={"error": str(e)},
                headers={},
                duration=duration
            )

    def test_connection(self) -> bool:
        """Test MongoDB connection."""
        try:
            self.client.server_info()
            return True
        except Exception:
            return False
```

### Configuration

Add MongoDB service to config:

```yaml
services:
  my-mongo:
    dev:
      provider: mongodb
      connection_string: mongodb://localhost:27017
      database: mydb
    aliases:
      users: users  # Collection name
      orders: orders
```

### Usage in REPL

```bash
# Find documents
nodi> find users query='{"active": true}' limit=10

# Insert document
nodi> insert users {"name": "John", "email": "john@example.com"}

# Update documents
nodi> update users query='{"name": "John"}' {"active": true}

# Delete documents
nodi> delete users query='{"active": false}'
```

## More Provider Examples

### Example: Elasticsearch Provider

```python
# nodi/providers/elasticsearch.py

from elasticsearch import Elasticsearch
from nodi.providers.base import DataProvider, ProviderRequest, ProviderResponse

class ElasticsearchProvider(DataProvider):
    """Elasticsearch data provider."""

    def __init__(self, name: str = "elasticsearch", config: Dict[str, Any] = None):
        super().__init__(name, config)
        self.client = Elasticsearch(
            hosts=[config.get("host", "localhost:9200")]
        )

    def request(self, request: ProviderRequest) -> ProviderResponse:
        """Execute Elasticsearch operation."""
        import time
        start_time = time.time()

        try:
            method = request.method.upper()
            index = request.resource

            if method == "SEARCH":
                # Search documents
                body = request.body or {}
                result = self.client.search(index=index, body=body)
                data = result["hits"]["hits"]
                status_code = 200

            elif method == "INDEX":
                # Index document
                doc = request.body
                result = self.client.index(index=index, body=doc)
                data = result
                status_code = 201

            duration = time.time() - start_time

            return ProviderResponse(
                status_code=status_code,
                data=data,
                headers={},
                duration=duration
            )

        except Exception as e:
            duration = time.time() - start_time
            return ProviderResponse(
                status_code=500,
                data={"error": str(e)},
                headers={},
                duration=duration
            )

    def test_connection(self) -> bool:
        """Test Elasticsearch connection."""
        return self.client.ping()
```

### Example: Redis Provider

```python
# nodi/providers/redis.py

import redis
from nodi.providers.base import DataProvider, ProviderRequest, ProviderResponse

class RedisProvider(DataProvider):
    """Redis data provider."""

    def __init__(self, name: str = "redis", config: Dict[str, Any] = None):
        super().__init__(name, config)
        self.client = redis.Redis(
            host=config.get("host", "localhost"),
            port=config.get("port", 6379),
            db=config.get("database", 0)
        )

    def request(self, request: ProviderRequest) -> ProviderResponse:
        """Execute Redis operation."""
        import time
        start_time = time.time()

        try:
            method = request.method.upper()
            key = request.resource

            if method == "GET":
                value = self.client.get(key)
                data = value.decode() if value else None
                status_code = 200 if value else 404

            elif method == "SET":
                value = request.body
                ttl = request.params.get("ttl")
                self.client.set(key, value, ex=ttl)
                data = {"ok": True}
                status_code = 200

            elif method == "DELETE":
                result = self.client.delete(key)
                data = {"deleted": result}
                status_code = 200

            duration = time.time() - start_time

            return ProviderResponse(
                status_code=status_code,
                data=data,
                headers={},
                duration=duration
            )

        except Exception as e:
            duration = time.time() - start_time
            return ProviderResponse(
                status_code=500,
                data={"error": str(e)},
                headers={},
                duration=duration
            )

    def test_connection(self) -> bool:
        """Test Redis connection."""
        return self.client.ping()
```

## Registering Custom Providers

### 1. Create Provider File

Place in `nodi/providers/your_provider.py`

### 2. Register in Provider Manager

```python
# nodi/providers/manager.py

from nodi.providers.mongodb import MongoDBProvider
from nodi.providers.elasticsearch import ElasticsearchProvider
from nodi.providers.redis import RedisProvider

PROVIDER_REGISTRY = {
    "rest": RestProvider,
    "mongodb": MongoDBProvider,
    "elasticsearch": ElasticsearchProvider,
    "redis": RedisProvider,
    # Add your provider here
}
```

### 3. Update Configuration Schema

Allow `provider` field in service config:

```yaml
services:
  my-data:
    dev:
      provider: mongodb  # or elasticsearch, redis, etc.
      # Provider-specific config
      connection_string: ...
```

## Provider Best Practices

### ✅ Do

- Extend `DataProvider` base class
- Implement `request()` and `test_connection()` methods
- Handle errors gracefully
- Return consistent `ProviderResponse` format
- Add type hints
- Document configuration options
- Write tests for your provider

### ❌ Don't

- Throw unhandled exceptions
- Block indefinitely (use timeouts)
- Ignore configuration
- Modify global state
- Skip connection testing

---

# Scripting System

## Script Architecture

The scripting system consists of three layers:

1. **Parser** (`parser.py`): Converts `.nodi` text to instructions
2. **Engine** (`engine.py`): Executes parsed instructions
3. **Suite Runner** (`suite.py`): Orchestrates multiple scripts

### Script Parser

The parser converts text to executable instructions:

```python
# nodi/scripting/parser.py

from dataclasses import dataclass
from typing import List, Dict, Any

@dataclass
class ScriptLine:
    line_number: int
    line_type: str  # 'assignment', 'http', 'assert', 'echo', 'print'
    content: Dict[str, Any]
    raw_line: str

class ScriptParser:
    def parse(self, script_content: str) -> List[ScriptLine]:
        """Parse script into executable lines."""
        # Implementation
        pass
```

### Script Engine

The engine executes parsed instructions:

```python
# nodi/scripting/engine.py

class ScriptEngine:
    def __init__(self, config, rest_provider, resolver):
        self.config = config
        self.rest_provider = rest_provider
        self.resolver = resolver
        self.variables = {}  # Isolated scope

    def run_script(self, script_path: str, params: Dict = None):
        """Execute a script file."""
        # Parse script
        # Execute lines
        # Return results
        pass
```

## Extending the Scripting System

### Adding New Statement Types

**1. Add to Parser**:

```python
# nodi/scripting/parser.py

def _parse_line(self, line: str, line_num: int):
    # Existing statements...

    # Add new statement type
    if stripped.startswith('wait '):
        duration = stripped[5:].strip()
        return ScriptLine(
            line_number=line_num,
            line_type='wait',
            content={'duration': duration},
            raw_line=line
        )
```

**2. Add to Engine**:

```python
# nodi/scripting/engine.py

def _execute_line(self, line: ScriptLine):
    if line.line_type == 'wait':
        return self._execute_wait(line)
    # ... other types

def _execute_wait(self, line: ScriptLine):
    """Execute wait/delay command."""
    import time
    duration_str = line.content['duration']

    # Parse duration (e.g., "2s", "500ms")
    if duration_str.endswith('ms'):
        duration = float(duration_str[:-2]) / 1000
    elif duration_str.endswith('s'):
        duration = float(duration_str[:-1])
    else:
        duration = float(duration_str)

    time.sleep(duration)
    return f"Waited {duration}s"
```

**3. Use in Scripts**:

```nodi
# test_with_delay.nodi
GET user:1
wait 2s
GET user:1
```

### Adding Custom Script Functions

**1. Create Function Library**:

```python
# nodi/scripting/functions.py

class ScriptFunctions:
    """Custom functions available in scripts."""

    @staticmethod
    def random_string(length: int = 10) -> str:
        """Generate random string."""
        import random
        import string
        return ''.join(random.choices(string.ascii_letters, k=length))

    @staticmethod
    def timestamp() -> str:
        """Get current timestamp."""
        import datetime
        return datetime.datetime.now().isoformat()

    @staticmethod
    def uuid() -> str:
        """Generate UUID."""
        import uuid
        return str(uuid.uuid4())
```

**2. Register in Engine**:

```python
# nodi/scripting/engine.py

from .functions import ScriptFunctions

class ScriptEngine:
    def __init__(self, ...):
        # ...
        self.functions = ScriptFunctions()

    def _evaluate_expression(self, expr: str):
        # Add function call support
        if expr.startswith('fn.'):
            func_name = expr[3:]
            if hasattr(self.functions, func_name):
                return getattr(self.functions, func_name)()
        # ... existing logic
```

**3. Use in Scripts**:

```nodi
# Create user with random data
$random_id = fn.random_string()
$timestamp = fn.timestamp()

POST users {"id": "$random_id", "created_at": "$timestamp"}
```

### Adding Control Flow

**1. Implement if/else**:

```python
# nodi/scripting/engine.py

def _execute_if(self, lines: List[ScriptLine], index: int):
    """Execute if block."""
    condition = lines[index].content['condition']

    # Evaluate condition
    result = self._evaluate_assertion(condition)

    # Find end of if block
    end_index = self._find_block_end(lines, index)

    if result:
        # Execute if block
        for i in range(index + 1, end_index):
            self._execute_line(lines[i])
    else:
        # Find else block and execute
        else_index = self._find_else(lines, index, end_index)
        if else_index:
            for i in range(else_index + 1, end_index):
                self._execute_line(lines[i])
```

**2. Use in Scripts**:

```nodi
GET user:$user_id

if $data.active == true
    echo "User is active"
    GET user:$user_id/orders
else
    echo "User is inactive"
end
```

### Adding Loops

**1. Implement for loop**:

```python
def _execute_for(self, lines: List[ScriptLine], index: int):
    """Execute for loop."""
    var_name = lines[index].content['variable']
    iterable = self._evaluate_expression(lines[index].content['iterable'])

    # Find end of loop
    end_index = self._find_block_end(lines, index)

    # Execute loop body for each item
    for item in iterable:
        self.variables[var_name] = item
        for i in range(index + 1, end_index):
            self._execute_line(lines[i])
```

**2. Use in Scripts**:

```nodi
GET users | .[0:5]
$users = $data

for $user in $users
    echo "Processing user: $user.name"
    GET user:$user.id/orders
    print $data
end
```

## Script Testing

### Unit Testing Scripts

```python
# tests/test_scripts.py

def test_simple_script():
    """Test basic script execution."""
    script = """
    $x = 10
    assert $x == 10
    """

    engine = ScriptEngine(config, provider, resolver)
    result = engine.run_script_content(script)

    assert result['status'] == 'PASS'

def test_script_with_http():
    """Test script with HTTP requests."""
    script = """
    GET users
    assert $response.status_code == 200
    """

    # Mock HTTP provider
    # Execute script
    # Assert results
```

### Integration Testing

```python
def test_full_workflow():
    """Test complete workflow."""
    # Create test script
    # Run script
    # Verify results
    # Cleanup
```

---

# Adding Features

## Adding REPL Commands

**1. Add handler**:

```python
# nodi/repl.py

def _handle_my_command(self, parts):
    """Handle my-command."""
    if len(parts) < 2:
        print("Usage: my-command <arg>")
        return

    arg = parts[1]
    # Implementation
    print(f"Executed with: {arg}")
```

**2. Register command**:

```python
def _process_command(self, command: str):
    # ...
    elif cmd == "my-command":
        self._handle_my_command(parts)
```

**3. Add to completer**:

```python
def _get_completer(self):
    commands = [
        # ... existing
        "my-command",
    ]
```

**4. Update help**:

```python
def _show_help(self):
    help_text = """
    ...
    My Commands:
      my-command <arg>     Description of command
    """
```

## Adding Output Formatters

**1. Create formatter**:

```python
# nodi/formatters/my_format.py

class MyFormatter:
    """Custom output formatter."""

    def format(self, data: Any) -> str:
        """Format data."""
        # Implementation
        return formatted_string
```

**2. Register**:

```python
# nodi/formatters/__init__.py

from .my_format import MyFormatter

__all__ = [..., "MyFormatter"]
```

**3. Add to REPL**:

```python
# nodi/repl.py

from nodi.formatters.my_format import MyFormatter

self.my_formatter = MyFormatter()

# In _handle_format()
elif format_name == "myformat":
    self.my_formatter = MyFormatter()
```

---

# Development Workflow

## Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=nodi --cov-report=html

# Run specific test file
pytest tests/test_config.py

# Run specific test
pytest tests/test_config.py::test_config_get_service

# Run with verbose output
pytest -v

# Stop on first failure
pytest -x
```

## Code Quality

### Formatting

```bash
# Format code
black nodi/

# Check formatting
black --check nodi/

# Format specific file
black nodi/repl.py
```

### Linting

```bash
# Lint all files
flake8 nodi/

# Lint specific file
flake8 nodi/repl.py

# With specific rules
flake8 --max-line-length=100 nodi/
```

### Type Checking

```bash
# Type check all files
mypy nodi/

# Type check specific file
mypy nodi/config/models.py
```

## Manual Testing

```bash
# Test REPL
python -m nodi repl

# Test CLI
python -m nodi request service.env@endpoint

# Test with custom config
python -m nodi --config examples/config.yml

# Test script execution
python -m nodi run test_script.nodi

# Enable debug mode
python -m nodi --debug repl
```

---

# Testing Guidelines

## Writing Tests

```python
import pytest
from nodi.config.models import Config, Service

def test_my_feature():
    """Test description."""
    # Arrange
    config = Config(...)

    # Act
    result = config.some_method()

    # Assert
    assert result == expected_value

def test_error_handling():
    """Test error cases."""
    with pytest.raises(ValueError):
        # Code that should raise
        pass
```

## Test Structure

```
tests/
├── test_config.py           # Config tests
├── test_repl.py             # REPL tests
├── test_providers.py        # Provider tests
├── test_scripting.py        # Script tests
├── test_integration.py      # Integration tests
└── fixtures/                # Test fixtures
    ├── sample_config.yml
    └── sample_script.nodi
```

## Mocking

```python
from unittest.mock import Mock, patch

def test_with_mock():
    """Test with mocked dependencies."""
    mock_provider = Mock()
    mock_provider.request.return_value = ProviderResponse(...)

    # Test with mock
    engine = ScriptEngine(config, mock_provider, resolver)
    result = engine.run_script("test.nodi")

    # Verify
    assert mock_provider.request.called
```

---

# Contributing

## Contribution Workflow

1. **Fork repository**
2. **Create feature branch**: `git checkout -b feature/my-feature`
3. **Make changes**
4. **Write tests**
5. **Run tests**: `pytest`
6. **Format code**: `black nodi/`
7. **Commit**: `git commit -m "Add my feature"`
8. **Push**: `git push origin feature/my-feature`
9. **Create pull request**

## Pull Request Guidelines

- Clear description of changes
- Tests for new features
- Documentation updates
- Follow code style
- All tests passing

## Code Style

- Follow PEP 8
- Use type hints
- Write docstrings
- Keep functions small
- Use meaningful names

---

**Development guide complete!** Start extending Nodi with custom providers and scripting features.
