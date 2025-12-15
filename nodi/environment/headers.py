"""Header management for Nodi."""

import re
from typing import Dict, Optional
from nodi.config.models import Config


class HeaderManager:
    """Manage HTTP headers for requests."""

    def __init__(self, config: Config):
        self.config = config
        self.session_headers: Dict[str, str] = {}
        self.var_pattern = re.compile(r"\$\{var:(\w+)\}")

    def get_headers(
        self,
        service: str,
        environment: str,
        additional_headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, str]:
        """
        Get merged headers for a request.

        Priority (highest to lowest):
        1. Additional headers (passed to this method)
        2. Session headers (set via set_header in REPL)
        3. Service-specific headers (from config)
        4. Environment-wide headers (from config)
        5. Default headers
        """
        headers = self._get_default_headers()

        # Environment-wide headers
        env_headers = self.config.get_environment_headers(environment)
        headers.update(env_headers)

        # Service-specific headers
        service_obj = self.config.get_service(service)
        if service_obj:
            env_config = service_obj.environments.get(environment)
            if env_config and env_config.headers:
                headers.update(env_config.headers)

        # Session headers
        headers.update(self.session_headers)

        # Additional headers
        if additional_headers:
            headers.update(additional_headers)

        # Resolve variable references at request time
        headers = self._resolve_variables(headers)

        return headers

    def set_session_header(self, name: str, value: str):
        """Set a header for the current session."""
        self.session_headers[name] = value

    def unset_session_header(self, name: str):
        """Remove a header from the current session."""
        self.session_headers.pop(name, None)

    def clear_session_headers(self):
        """Clear all session headers."""
        self.session_headers.clear()

    def get_session_headers(self) -> Dict[str, str]:
        """Get current session headers."""
        return self.session_headers.copy()

    def _get_default_headers(self) -> Dict[str, str]:
        """Get default headers for all requests."""
        return {
            "User-Agent": "nodi/0.1.0",
            "Accept": "application/json, */*",
        }

    def _resolve_variables(self, headers: Dict[str, str]) -> Dict[str, str]:
        """Resolve variable references in header values at request time."""
        resolved = {}
        for name, value in headers.items():
            resolved[name] = self._substitute_variable_string(value)
        return resolved

    def _substitute_variable_string(self, value: str) -> str:
        """Substitute custom variables in a string."""

        def replace(match):
            var_name = match.group(1)
            var_value = self.config.get_variable(var_name)
            return var_value if var_value is not None else match.group(0)

        return self.var_pattern.sub(replace, value)

    def set_variable(self, name: str, value: str):
        """Set a variable value in the config."""
        self.config.set_variable(name, value)

    def get_variable(self, name: str) -> Optional[str]:
        """Get a variable value from the config."""
        return self.config.get_variable(name)

    def list_variables(self) -> Dict[str, str]:
        """Get all variables."""
        return self.config.list_variables()

    def mask_sensitive_headers(self, headers: Dict[str, str]) -> Dict[str, str]:
        """Mask sensitive header values for display."""
        sensitive_patterns = [
            "authorization",
            "api-key",
            "api_key",
            "apikey",
            "token",
            "secret",
            "password",
            "cookie",
        ]

        masked = {}
        for name, value in headers.items():
            name_lower = name.lower()
            if any(pattern in name_lower for pattern in sensitive_patterns):
                # Show first 3 and last 3 characters
                if len(value) > 10:
                    masked[name] = f"{value[:3]}***{value[-3:]}"
                else:
                    masked[name] = "***"
            else:
                masked[name] = value

        return masked
