# Nodi Development Guide

This guide covers development setup, architecture, and contribution guidelines for Nodi.

## Development Setup

### Prerequisites

- Python 3.8 or higher
- pip
- virtualenv (recommended)

### Setup Steps

```bash
# Clone repository
git clone https://github.com/yourusername/nodi.git
cd nodi

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On Unix/macOS:
source venv/bin/activate

# Install in development mode with all dependencies
pip install -e .[dev,full]
```

## Project Structure

```
nodi/
├── nodi/                      # Main package
│   ├── __init__.py           # Package initialization
│   ├── __main__.py           # Entry point
│   ├── cli.py                # CLI interface (Click)
│   ├── repl.py               # Interactive REPL
│   ├── config/               # Configuration management
│   │   ├── loader.py         # Config file loading & merging
│   │   ├── models.py         # Data models
│   │   └── validator.py      # Config validation
│   ├── environment/          # Service/environment management
│   │   ├── manager.py        # Context management
│   │   ├── resolver.py       # URL resolution
│   │   └── headers.py        # Header management
│   ├── providers/            # Data provider system
│   │   ├── base.py           # Base provider class
│   │   ├── manager.py        # Provider manager
│   │   └── rest.py           # REST/HTTP provider
│   ├── formatters/           # Output formatters
│   │   ├── json.py           # JSON formatter
│   │   ├── yaml_fmt.py       # YAML formatter
│   │   ├── table.py          # Table formatter
│   │   └── csv_fmt.py        # CSV formatter
│   ├── filters.py            # jq-style filtering
│   ├── history.py            # Request history
│   ├── certificates.py       # SSL/TLS management
│   └── utils/                # Utilities
│       ├── color.py          # Terminal colors
│       └── validators.py     # Validators
├── tests/                    # Test suite
├── examples/                 # Example configurations
├── docs/                     # Documentation
├── setup.py                  # Package setup
├── pyproject.toml            # Project metadata
└── requirements.txt          # Dependencies
```

## Architecture

### Core Components

#### 1. Configuration System

- **ConfigLoader**: Loads and merges configs from multiple sources
- **Config/Service/ServiceEnvironment**: Data models
- **ConfigValidator**: Validates configuration

#### 2. Environment Management

- **EnvironmentManager**: Manages current service/environment context
- **URLResolver**: Parses `service.env@endpoint` syntax
- **HeaderManager**: Manages HTTP headers

#### 3. Provider System

- **DataProvider**: Abstract base for data sources
- **RestProvider**: HTTP/REST implementation
- **ProviderManager**: Manages provider instances

Extensible architecture allows adding providers for:
- Databases (MongoDB, PostgreSQL)
- Message queues (Kafka, RabbitMQ)
- Log systems (Elasticsearch, Splunk)

#### 4. REPL Interface

- Built with `prompt_toolkit`
- Auto-completion
- History
- Syntax highlighting

#### 5. Formatters

- JSON (with syntax highlighting)
- YAML
- ASCII tables
- CSV

## Development Workflow

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=nodi --cov-report=html

# Run specific test file
pytest tests/test_config.py

# Run specific test
pytest tests/test_config.py::test_config_get_service
```

### Code Quality

```bash
# Format code
black nodi/

# Check formatting
black --check nodi/

# Lint
flake8 nodi/

# Type checking
mypy nodi/
```

### Manual Testing

```bash
# Test REPL
python -m nodi

# Test CLI
python -m nodi request user-service.dev@users

# Test with custom config
python -m nodi --config examples/config/example-config.yml
```

## Adding Features

### Adding a New Command to REPL

1. Add command handler in `nodi/repl.py`:

```python
def _handle_my_command(self, parts):
    """Handle my-command."""
    # Implementation
    pass
```

2. Add to command processing in `_process_command()`:

```python
elif cmd == "my-command":
    self._handle_my_command(parts)
```

3. Add to completer in `_get_completer()`:

```python
commands = [
    # ... existing commands
    "my-command",
]
```

4. Update help text in `_show_help()`.

### Adding a New Output Formatter

1. Create `nodi/formatters/my_format.py`:

```python
class MyFormatter:
    def format(self, data):
        # Implementation
        return formatted_string
```

2. Register in `nodi/formatters/__init__.py`:

```python
from nodi.formatters.my_format import MyFormatter

__all__ = [..., "MyFormatter"]
```

3. Add to REPL and CLI format options.

### Adding a New Provider

1. Create `nodi/providers/my_provider.py`:

```python
from nodi.providers.base import DataProvider, ProviderRequest, ProviderResponse

class MyProvider(DataProvider):
    def request(self, request: ProviderRequest) -> ProviderResponse:
        # Implementation
        pass

    def test_connection(self) -> bool:
        # Implementation
        pass
```

2. Register in provider manager.

3. Add configuration support.

## Testing Guidelines

### Writing Tests

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
```

### Test Categories

- **Unit tests**: Test individual functions/methods
- **Integration tests**: Test component interactions
- **End-to-end tests**: Test full workflows

### Running Specific Test Categories

```bash
# Unit tests only
pytest tests/test_config.py

# Integration tests
pytest tests/test_integration.py
```

## Code Style

### Python Style Guide

- Follow PEP 8
- Use Black for formatting (line length: 100)
- Use type hints where appropriate
- Write docstrings for public APIs

### Example

```python
from typing import Optional, Dict

def get_service_info(service_name: str) -> Optional[Dict]:
    """
    Get information about a service.

    Args:
        service_name: Name of the service

    Returns:
        Service information dict or None if not found
    """
    # Implementation
    pass
```

### Commit Messages

Follow conventional commits:

```
feat: Add jq filtering support
fix: Fix URL resolution for path parameters
docs: Update README with examples
test: Add tests for ConfigValidator
refactor: Simplify header management
```

## Debugging

### Enable Verbose Logging

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Debug REPL

```bash
python -m pdb -m nodi
```

### Debug Specific Request

```python
from nodi.config.loader import ConfigLoader
from nodi.environment.manager import EnvironmentManager

config = ConfigLoader().load()
env_mgr = EnvironmentManager(config)

spec, url = env_mgr.resolve_url("user-service.dev@users")
print(f"Spec: {spec}")
print(f"URL: {url}")
```

## Release Process

1. Update version in `nodi/__init__.py`
2. Update version in `pyproject.toml`
3. Update CHANGELOG.md
4. Create git tag: `git tag v0.1.0`
5. Push tag: `git push origin v0.1.0`
6. Build package: `python -m build`
7. Upload to PyPI: `python -m twine upload dist/*`

## Contributing

### Pull Request Process

1. Fork the repository
2. Create feature branch: `git checkout -b feature/my-feature`
3. Make changes
4. Add tests
5. Run tests and linters
6. Commit with conventional commit message
7. Push to fork
8. Create pull request

### Code Review Checklist

- [ ] Tests added/updated
- [ ] Documentation updated
- [ ] Code formatted (black)
- [ ] Linting passes (flake8)
- [ ] Type hints added (mypy)
- [ ] Examples added if needed

## Common Development Tasks

### Add New Dependency

```bash
# Add to pyproject.toml [project.dependencies]
# Then reinstall
pip install -e .
```

### Update Documentation

1. Update README.md for user-facing changes
2. Update DEVELOPMENT.md for developer changes
3. Update docstrings in code
4. Update examples if needed

### Profile Performance

```bash
python -m cProfile -o profile.stats -m nodi request user-service.dev@users
python -m pstats profile.stats
```

## Resources

- [Click Documentation](https://click.palletsprojects.com/)
- [prompt_toolkit Documentation](https://python-prompt-toolkit.readthedocs.io/)
- [httpx Documentation](https://www.python-httpx.org/)
- [Rich Documentation](https://rich.readthedocs.io/)
- [pytest Documentation](https://docs.pytest.org/)

## Getting Help

- GitHub Issues: https://github.com/yourusername/nodi/issues
- Discussions: https://github.com/yourusername/nodi/discussions
