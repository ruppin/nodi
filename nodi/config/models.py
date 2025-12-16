"""Configuration data models for Nodi."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from pathlib import Path


@dataclass
class ServiceEnvironment:
    """Configuration for a specific service environment (dev/qa/prod)."""

    base_url: str
    headers: Optional[Dict[str, str]] = None
    timeout: Optional[int] = 30
    verify_ssl: bool = True


@dataclass
class Service:
    """Configuration for a microservice."""

    name: str
    environments: Dict[str, ServiceEnvironment]
    aliases: Dict[str, str] = field(default_factory=dict)
    description: Optional[str] = None


@dataclass
class EnvironmentHeaders:
    """Headers configuration for an environment."""

    headers: Dict[str, str] = field(default_factory=dict)


@dataclass
class Certificates:
    """SSL/TLS certificate configuration for an environment."""

    cert: Optional[str] = None
    key: Optional[str] = None
    ca: Optional[str] = None
    verify: bool = True
    ssl_version: Optional[str] = None

    def expand_paths(self, base_path: Optional[Path] = None) -> "Certificates":
        """Expand certificate file paths with home directory and base path."""
        if base_path is None:
            base_path = Path.home()

        cert_path = None
        if self.cert:
            cert_path = Path(self.cert).expanduser()
            if not cert_path.is_absolute() and base_path:
                cert_path = base_path / cert_path
            cert_path = str(cert_path)

        key_path = None
        if self.key:
            key_path = Path(self.key).expanduser()
            if not key_path.is_absolute() and base_path:
                key_path = base_path / key_path
            key_path = str(key_path)

        ca_path = None
        if self.ca:
            ca_path = Path(self.ca).expanduser()
            if not ca_path.is_absolute() and base_path:
                ca_path = base_path / ca_path
            ca_path = str(ca_path)

        return Certificates(
            cert=cert_path,
            key=key_path,
            ca=ca_path,
            verify=self.verify,
            ssl_version=self.ssl_version,
        )


@dataclass
class Config:
    """Main configuration for Nodi."""

    services: Dict[str, Service] = field(default_factory=dict)
    headers: Dict[str, EnvironmentHeaders] = field(default_factory=dict)
    certificates: Dict[str, Certificates] = field(default_factory=dict)
    default_environment: str = "dev"
    default_service: Optional[str] = None
    service_aliases: Dict[str, str] = field(default_factory=dict)
    profiles: Dict[str, Dict] = field(default_factory=dict)
    variables: Dict[str, str] = field(default_factory=dict)
    filters: Dict[str, str] = field(default_factory=dict)
    projections: Dict[str, Any] = field(default_factory=dict)

    def get_service(self, service_name: str) -> Optional[Service]:
        """Get service by name or alias."""
        # Try direct lookup
        if service_name in self.services:
            return self.services[service_name]

        # Try alias lookup
        if service_name in self.service_aliases:
            actual_name = self.service_aliases[service_name]
            return self.services.get(actual_name)

        return None

    def get_environment_headers(self, environment: str) -> Dict[str, str]:
        """Get headers for a specific environment."""
        env_headers = self.headers.get(environment)
        if env_headers:
            return env_headers.headers.copy()
        return {}

    def get_certificates(self, environment: str) -> Optional[Certificates]:
        """Get certificates for a specific environment."""
        return self.certificates.get(environment)

    def list_services(self) -> List[str]:
        """Get list of all service names."""
        return list(self.services.keys())

    def list_environments(self, service_name: Optional[str] = None) -> List[str]:
        """Get list of all environments, optionally filtered by service."""
        if service_name:
            service = self.get_service(service_name)
            if service:
                return list(service.environments.keys())
            return []

        # Get all unique environments across all services
        all_envs = set()
        for service in self.services.values():
            all_envs.update(service.environments.keys())
        return sorted(list(all_envs))

    def get_variable(self, var_name: str) -> Optional[str]:
        """Get a variable value by name."""
        return self.variables.get(var_name)

    def set_variable(self, var_name: str, value: str):
        """Set a variable value."""
        self.variables[var_name] = value

    def list_variables(self) -> Dict[str, str]:
        """Get all variables."""
        return self.variables.copy()

    def get_filter(self, filter_name: str) -> Optional[str]:
        """Get a filter expression by name."""
        return self.filters.get(filter_name)

    def list_filters(self) -> Dict[str, str]:
        """Get all predefined filters."""
        return self.filters.copy()

    def get_projection(self, projection_name: str) -> Optional[Any]:
        """Get a projection specification by name."""
        return self.projections.get(projection_name)

    def list_projections(self) -> Dict[str, Any]:
        """Get all predefined projections."""
        return self.projections.copy()
