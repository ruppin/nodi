"""Configuration management for Nodi."""

from pathlib import Path
from typing import Any

import yaml


class Config:
    """Configuration manager for Nodi."""

    def __init__(self, config_path: Path | None = None) -> None:
        """Initialize configuration."""
        self.config_path = config_path or Path.home() / ".nodi" / "config.yml"
        self._data = self._load_config()
        self._environment = self._data.get("default_environment", "dev")

    def _load_config(self) -> dict[str, Any]:
        """Load configuration from YAML file."""
        if not self.config_path.exists():
            return {}
        
        with self.config_path.open() as f:
            return yaml.safe_load(f) or {}

    def set_environment(self, env: str) -> None:
        """Set the active environment."""
        self._environment = env

    def get_variables(self, var_set: str) -> dict[str, str]:
        """Get variable set by name.
        
        Args:
            var_set: Name of variable set (e.g., 'alice', 'bob')
            
        Returns:
            Dict of variable values
            
        Raises:
            ValueError: If variable set not found
        """
        variables = self._data.get("variables", {})
        if var_set not in variables:
            available = ", ".join(variables.keys()) or "none"
            msg = f"Variable set '{var_set}' not found. Available: {available}"
            raise ValueError(msg)
        return variables[var_set]

    def get_service_config(self, service: str) -> dict[str, Any]:
        """Get service configuration."""
        return self._data.get("services", {}).get(service, {})

    def get_environment_headers(self) -> dict[str, str]:
        """Get headers for current environment."""
        return self._data.get("headers", {}).get(self._environment, {})

    def get_alias(self, alias: str) -> dict[str, Any] | None:
        """Get alias configuration."""
        for service_config in self._data.get("services", {}).values():
            aliases = service_config.get("aliases", {})
            if alias in aliases:
                return aliases[alias]
        return None

    def get_service_for_alias(self, alias: str) -> str | None:
        """Get service name that contains the alias."""
        for service_name, service_config in self._data.get("services", {}).items():
            if alias in service_config.get("aliases", {}):
                return service_name
        return None