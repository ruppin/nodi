# Nodi Plugin Development Guide

Create custom plugins to extend Nodi's functionality.

## Quick Start

### 1. Create a Plugin

`~/.nodi/plugins/my_plugin.py`:

```python
from nodi.plugins import Plugin

class MyPlugin(Plugin):
    """My custom plugin."""

    @property
    def name(self) -> str:
        return "my_plugin"

    @property
    def description(self) -> str:
        return "My awesome plugin"

    def before_request(self, request):
        """Called before every HTTP request."""
        print(f"Making request to: {request.resource}")
        return request

    def after_response(self, response):
        """Called after every HTTP response."""
        print(f"Got response: {response.status_code}")
        return response
```

### 2. Load Plugin

In `config.yml`:

```yaml
plugins:
  - my_plugin.MyPlugin
```

Or load programmatically in Python scripts:

```python
from nodi.plugins import PluginManager

manager = PluginManager()
manager.add_plugin_path("~/.nodi/plugins")
manager.load_plugin("my_plugin.MyPlugin")
```

---

## Plugin Hooks

### Lifecycle Hooks

```python
class MyPlugin(Plugin):
    def on_load(self):
        """Called when plugin is loaded."""
        print("Plugin loaded!")

    def on_unload(self):
        """Called when plugin is unloaded."""
        print("Plugin unloaded!")
```

### Request/Response Hooks

```python
class MyPlugin(Plugin):
    def before_request(self, request):
        """Modify request before sending.

        Args:
            request: ProviderRequest object

        Returns:
            Modified request
        """
        request.headers['X-Custom'] = 'value'
        return request

    def after_response(self, response):
        """Process response after receiving.

        Args:
            response: ProviderResponse object

        Returns:
            Modified response
        """
        # Log response time
        print(f"Response time: {response.elapsed_time}ms")
        return response
```

### Error Hook

```python
class MyPlugin(Plugin):
    def on_error(self, error):
        """Handle errors.

        Args:
            error: Exception that occurred

        Returns:
            Modified exception or None to suppress
        """
        print(f"Error occurred: {error}")
        return error  # Or return None to suppress
```

### Data Transformation Hook

```python
class MyPlugin(Plugin):
    def transform_data(self, data):
        """Transform response data.

        Args:
            data: Response data

        Returns:
            Transformed data
        """
        # Add metadata
        if isinstance(data, dict):
            data['_processed'] = True
        return data
```

---

## Plugin Configuration

```yaml
plugins:
  - name: my_plugin.MyPlugin
    config:
      enabled: true
      api_key: ${MY_API_KEY}
      log_level: debug
      custom_setting: value
```

Access config in plugin:

```python
class MyPlugin(Plugin):
    def __init__(self, config=None):
        super().__init__(config)
        self.api_key = self.config.get('api_key')
        self.log_level = self.config.get('log_level', 'info')
```

---

## Example Plugins

### Authentication Plugin

```python
from nodi.plugins import Plugin

class AuthPlugin(Plugin):
    @property
    def name(self) -> str:
        return "auth"

    def __init__(self, config=None):
        super().__init__(config)
        self.token = self.config.get('token')

    def before_request(self, request):
        """Add auth header to all requests."""
        request.headers['Authorization'] = f'Bearer {self.token}'
        return request
```

### Logging Plugin

```python
from nodi.plugins import Plugin
from datetime import datetime

class RequestLoggerPlugin(Plugin):
    @property
    def name(self) -> str:
        return "logger"

    def before_request(self, request):
        timestamp = datetime.now().strftime('%H:%M:%S')
        print(f"[{timestamp}] {request.method} {request.resource}")
        return request

    def after_response(self, response):
        print(f"  → {response.status_code} ({response.elapsed_time:.0f}ms)")
        return response
```

### Rate Limiter Plugin

```python
from nodi.plugins import Plugin
import time

class RateLimiterPlugin(Plugin):
    @property
    def name(self) -> str:
        return "rate_limiter"

    def __init__(self, config=None):
        super().__init__(config)
        self.requests = []
        self.max_per_second = self.config.get('max_per_second', 10)

    def before_request(self, request):
        """Enforce rate limiting."""
        current = time.time()

        # Remove old requests
        self.requests = [t for t in self.requests if current - t < 1.0]

        # Check limit
        if len(self.requests) >= self.max_per_second:
            sleep_time = 1.0 - (current - min(self.requests))
            if sleep_time > 0:
                time.sleep(sleep_time)

        self.requests.append(time.time())
        return request
```

---

## See Also

- [Python Scripting Guide](PYTHON_SCRIPTING.md)
- [Examples](../examples/plugins/)
- [API Reference](API_REFERENCE.md)
