"""Python API for Nodi scripts.

Provides a clean Python interface for .py scripts to interact with Nodi.
"""

import json
from typing import Any, Dict, Optional, List, Union
from dataclasses import dataclass


@dataclass
class Response:
    """HTTP response wrapper with utility methods."""

    status_code: int
    headers: Dict[str, str]
    _data: Any
    _text: Optional[str] = None
    elapsed_ms: float = 0

    @property
    def ok(self) -> bool:
        """Check if response was successful (2xx)."""
        return 200 <= self.status_code < 300

    @property
    def is_error(self) -> bool:
        """Check if response was an error (4xx, 5xx)."""
        return self.status_code >= 400

    def json(self) -> Any:
        """Get response data as JSON."""
        return self._data

    def text(self) -> str:
        """Get response as text."""
        if self._text:
            return self._text
        if isinstance(self._data, str):
            return self._data
        return json.dumps(self._data)

    def assert_status(self, expected: int, message: Optional[str] = None):
        """Assert response status code."""
        if self.status_code != expected:
            msg = message or f"Expected status {expected}, got {self.status_code}"
            raise AssertionError(msg)

    def assert_ok(self, message: Optional[str] = None):
        """Assert response is successful (2xx)."""
        if not self.ok:
            msg = message or f"Expected 2xx status, got {self.status_code}"
            raise AssertionError(msg)


class HTTPClient:
    """HTTP client for Nodi Python scripts."""

    def __init__(self, rest_provider, resolver, config):
        """Initialize HTTP client.

        Args:
            rest_provider: RestProvider instance
            resolver: URLResolver instance
            config: Config instance
        """
        self.rest_provider = rest_provider
        self.resolver = resolver
        self.config = config
        self._session_headers: Dict[str, str] = {}

    def get(self, endpoint: str, **kwargs) -> Response:
        """HTTP GET request.

        Args:
            endpoint: Endpoint or alias
            **kwargs: Additional options (params, headers, etc.)

        Returns:
            Response object
        """
        return self._request('GET', endpoint, **kwargs)

    def post(self, endpoint: str, json: Optional[Dict] = None, data: Optional[Any] = None, **kwargs) -> Response:
        """HTTP POST request.

        Args:
            endpoint: Endpoint or alias
            json: JSON data to send
            data: Raw data to send
            **kwargs: Additional options (params, headers, etc.)

        Returns:
            Response object
        """
        return self._request('POST', endpoint, json=json, data=data, **kwargs)

    def put(self, endpoint: str, json: Optional[Dict] = None, data: Optional[Any] = None, **kwargs) -> Response:
        """HTTP PUT request."""
        return self._request('PUT', endpoint, json=json, data=data, **kwargs)

    def patch(self, endpoint: str, json: Optional[Dict] = None, data: Optional[Any] = None, **kwargs) -> Response:
        """HTTP PATCH request."""
        return self._request('PATCH', endpoint, json=json, data=data, **kwargs)

    def delete(self, endpoint: str, **kwargs) -> Response:
        """HTTP DELETE request."""
        return self._request('DELETE', endpoint, **kwargs)

    def head(self, endpoint: str, **kwargs) -> Response:
        """HTTP HEAD request."""
        return self._request('HEAD', endpoint, **kwargs)

    def options(self, endpoint: str, **kwargs) -> Response:
        """HTTP OPTIONS request."""
        return self._request('OPTIONS', endpoint, **kwargs)

    def set_header(self, name: str, value: str):
        """Set session header for all requests."""
        self._session_headers[name] = value

    def unset_header(self, name: str):
        """Remove session header."""
        self._session_headers.pop(name, None)

    def get_headers(self) -> Dict[str, str]:
        """Get current session headers."""
        return self._session_headers.copy()

    def _request(self, method: str, endpoint: str,
                 json: Optional[Dict] = None,
                 data: Optional[Any] = None,
                 params: Optional[Dict] = None,
                 headers: Optional[Dict] = None,
                 **kwargs) -> Response:
        """Internal request method.

        Args:
            method: HTTP method
            endpoint: Endpoint or alias
            json: JSON data
            data: Raw data
            params: Query parameters
            headers: Request headers
            **kwargs: Additional options

        Returns:
            Response object
        """
        from nodi.providers.base import ProviderRequest

        # Resolve endpoint
        resolved = self.resolver.resolve(endpoint, method)

        # Merge headers
        merged_headers = resolved.headers.copy()
        merged_headers.update(self._session_headers)
        if headers:
            merged_headers.update(headers)

        # Prepare data
        request_data = None
        if json is not None:
            request_data = json
        elif data is not None:
            request_data = data
        elif resolved.body:
            request_data = resolved.body

        # Merge params
        merged_params = resolved.params.copy() if resolved.params else {}
        if params:
            merged_params.update(params)

        # Create request
        request = ProviderRequest(
            method=resolved.method,
            resource=resolved.url,
            headers=merged_headers,
            params=merged_params if merged_params else None,
            data=request_data,
            timeout=kwargs.get('timeout')
        )

        # Execute request
        response = self.rest_provider.request(request)

        # Return wrapped response
        return Response(
            status_code=response.status_code,
            headers=response.headers or {},
            _data=response.data,
            elapsed_ms=response.elapsed_time or 0
        )


class NodiPythonAPI:
    """Main API for Nodi Python scripts."""

    def __init__(self, rest_provider, resolver, config, variables: Optional[Dict] = None):
        """Initialize Nodi Python API.

        Args:
            rest_provider: RestProvider instance
            resolver: URLResolver instance
            config: Config instance
            variables: Script variables
        """
        self.client = HTTPClient(rest_provider, resolver, config)
        self.config = config
        self.vars = variables or {}
        self._filters = None
        self._projections = None

    @property
    def filters(self):
        """Get filters module."""
        if self._filters is None:
            from nodi.filters import JSONFilter
            self._filters = JSONFilter()
        return self._filters

    @property
    def projections(self):
        """Get projections module."""
        if self._projections is None:
            from nodi.projections import JSONProjection
            self._projections = JSONProjection()
        return self._projections

    def apply_filter(self, data: Any, filter_expr: str) -> Any:
        """Apply jq filter to data.

        Args:
            data: Input data
            filter_expr: jq filter expression

        Returns:
            Filtered data
        """
        return self.filters.apply(data, filter_expr)

    def apply_projection(self, data: Any, projection_name: str) -> Any:
        """Apply predefined projection to data.

        Args:
            data: Input data
            projection_name: Name of projection from config

        Returns:
            Projected data
        """
        projection_spec = self.config.get_projection(projection_name)
        if not projection_spec:
            raise ValueError(f"Unknown projection: {projection_name}")
        return self.projections.apply(data, projection_spec)

    def get_filter(self, filter_name: str) -> Optional[str]:
        """Get predefined filter expression.

        Args:
            filter_name: Name of filter from config

        Returns:
            Filter expression or None
        """
        return self.config.get_filter(filter_name)

    def get_variable(self, name: str, default: Any = None) -> Any:
        """Get variable value.

        Args:
            name: Variable name
            default: Default value if not found

        Returns:
            Variable value
        """
        return self.vars.get(name, default)

    def set_variable(self, name: str, value: Any):
        """Set variable value.

        Args:
            name: Variable name
            value: Variable value
        """
        self.vars[name] = value

    def echo(self, *args, **kwargs):
        """Print message (alias for print)."""
        print(*args, **kwargs)

    def log(self, message: str, level: str = 'INFO'):
        """Log message.

        Args:
            message: Message to log
            level: Log level (INFO, WARNING, ERROR)
        """
        prefix = f"[{level}]"
        print(f"{prefix} {message}")
