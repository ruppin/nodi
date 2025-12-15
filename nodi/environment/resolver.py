"""URL resolution for service.env@endpoint syntax."""

import re
from dataclasses import dataclass
from typing import Optional, Dict, Tuple
from nodi.config.models import Config, Service


@dataclass
class RequestSpec:
    """Specification for a request parsed from user input."""

    service: str
    environment: str
    endpoint: str
    method: str = "GET"
    query_params: Optional[Dict[str, str]] = None
    path_params: Optional[Dict[str, str]] = None

    def __str__(self):
        return f"{self.service}.{self.environment}@{self.method}:{self.endpoint}"


class URLResolver:
    """Resolves service.env@endpoint syntax to full URLs."""

    def __init__(self, config: Config):
        self.config = config
        # Pattern: [service][.env][@][method:]endpoint[?params]
        self.pattern = re.compile(
            r"^(?:(?P<service>[\w-]+)(?:\.(?P<env>[\w-]+))?@)?"
            r"(?:(?P<method>GET|POST|PUT|PATCH|DELETE|HEAD|OPTIONS):)?"
            r"(?P<endpoint>[^\s?]+)"
            r"(?:\?(?P<query>.+))?$",
            re.IGNORECASE,
        )

    def parse(
        self,
        input_str: str,
        default_service: Optional[str] = None,
        default_env: Optional[str] = None,
    ) -> RequestSpec:
        """
        Parse user input into RequestSpec.

        Examples:
            user-service.dev@users
            user-service@users  (uses default env)
            users  (uses default service and env)
            order-service.qa@post:orders
            user-service@user:123
            user-service@search?q=john&status=active
        """
        match = self.pattern.match(input_str.strip())

        if not match:
            raise ValueError(f"Invalid request format: {input_str}")

        service = match.group("service") or default_service
        environment = match.group("env") or default_env
        method = (match.group("method") or "GET").upper()
        endpoint = match.group("endpoint")
        query_string = match.group("query")

        if not service:
            raise ValueError("Service not specified and no default service set")

        if not environment:
            raise ValueError("Environment not specified and no default environment set")

        # Parse query parameters
        query_params = None
        if query_string:
            query_params = self._parse_query_string(query_string)

        # Get service config to resolve alias path for parameter detection
        service_obj = self.config.get_service(service)
        alias_path = None
        if service_obj:
            # Try to get the alias path before extracting params
            endpoint_without_params = endpoint.split(":")[0]
            if endpoint_without_params in service_obj.aliases:
                alias_path = service_obj.aliases[endpoint_without_params]

        # Parse path parameters from endpoint (e.g., user:123 -> {id: 123})
        endpoint, path_params = self._extract_path_params(endpoint, alias_path)

        return RequestSpec(
            service=service,
            environment=environment,
            endpoint=endpoint,
            method=method,
            query_params=query_params,
            path_params=path_params,
        )

    def resolve(self, spec: RequestSpec) -> str:
        """
        Resolve RequestSpec to full URL.

        Process:
        1. Get service configuration
        2. Get environment base URL
        3. Resolve endpoint alias
        4. Substitute path parameters
        5. Append query parameters
        """
        # Get service
        service = self.config.get_service(spec.service)
        if not service:
            raise ValueError(f"Service not found: {spec.service}")

        # Get environment
        env_config = service.environments.get(spec.environment)
        if not env_config:
            raise ValueError(
                f"Environment '{spec.environment}' not found for service '{spec.service}'"
            )

        # Resolve endpoint (check aliases)
        path = self._resolve_endpoint(service, spec.endpoint)

        # Substitute path parameters
        if spec.path_params:
            path = self._substitute_path_params(path, spec.path_params)

        # Build full URL
        base_url = env_config.base_url.rstrip("/")
        full_path = path if path.startswith("/") else "/" + path
        url = f"{base_url}{full_path}"

        # Add query parameters
        if spec.query_params:
            query_string = "&".join(f"{k}={v}" for k, v in spec.query_params.items())
            url = f"{url}?{query_string}"

        return url

    def _resolve_endpoint(self, service: Service, endpoint: str) -> str:
        """Resolve endpoint alias to actual path."""
        # Check if endpoint is an alias
        if endpoint in service.aliases:
            return service.aliases[endpoint]

        # Not an alias, return as-is
        return endpoint

    def _extract_path_params(self, endpoint: str, alias_path: Optional[str] = None) -> Tuple[str, Optional[Dict[str, str]]]:
        """
        Extract path parameters from endpoint and auto-detect parameter name from alias.

        Examples:
            endpoint="user:123", alias_path="/users/{id}" -> (user, {id: 123})
            endpoint="user:123", alias_path="/users/{userId}" -> (user, {userId: 123})
            endpoint="doc:abc", alias_path="/documents/{documentId}" -> (doc, {documentId: abc})
            endpoint="users:123:profile" -> (users:profile, {id: 123})
            endpoint="orders" -> (orders, None)
        """
        # Pattern: alias:value or alias:value:rest
        parts = endpoint.split(":")

        if len(parts) == 1:
            # No path params
            return endpoint, None

        # Extract first parameter value
        alias = parts[0]
        param_value = parts[1]

        # If there are more parts, reconstruct the rest
        if len(parts) > 2:
            rest = ":".join(parts[2:])
            alias = f"{alias}:{rest}"

        # Auto-detect parameter name from alias path
        # Find first {param_name} in the alias path
        param_name = "id"  # Default to 'id'
        if alias_path:
            param_pattern = re.compile(r'\{(\w+)\}')
            match = param_pattern.search(alias_path)
            if match:
                param_name = match.group(1)  # Extract parameter name (e.g., "userId", "documentId")

        return alias, {param_name: param_value}

    def _substitute_path_params(self, path: str, params: Dict[str, str]) -> str:
        """Substitute path parameters in URL template."""
        # Replace {param} with values
        for param_name, param_value in params.items():
            path = path.replace(f"{{{param_name}}}", str(param_value))

        return path

    def _parse_query_string(self, query_string: str) -> Dict[str, str]:
        """Parse query string into dict."""
        params = {}
        for pair in query_string.split("&"):
            if "=" in pair:
                key, value = pair.split("=", 1)
                params[key] = value
            else:
                params[pair] = ""
        return params

    def parse_query_params(self, *args) -> Dict[str, str]:
        """
        Parse query parameters from arguments.

        Examples:
            parse_query_params("q=john", "status=active")
            -> {"q": "john", "status": "active"}
        """
        params = {}
        for arg in args:
            if "=" in arg:
                key, value = arg.split("=", 1)
                params[key] = value
        return params
