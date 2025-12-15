"""Environment and service context management."""

from typing import Optional, Dict
from nodi.config.models import Config, Certificates
from nodi.environment.headers import HeaderManager
from nodi.environment.resolver import URLResolver, RequestSpec


class EnvironmentManager:
    """Manages current service and environment context."""

    def __init__(self, config: Config):
        self.config = config
        self.current_service = config.default_service
        self.current_environment = config.default_environment
        self.header_manager = HeaderManager(config)
        self.url_resolver = URLResolver(config)

    def switch_service(self, service: str) -> bool:
        """
        Switch to a different service.

        Returns:
            True if successful, False if service not found
        """
        service_obj = self.config.get_service(service)
        if not service_obj:
            return False

        self.current_service = service_obj.name
        return True

    def switch_environment(self, environment: str) -> bool:
        """
        Switch to a different environment.

        Returns:
            True if successful, False if environment not found
        """
        # Validate environment exists for current service
        if self.current_service:
            service = self.config.get_service(self.current_service)
            if service and environment not in service.environments:
                return False

        self.current_environment = environment
        return True

    def switch_context(self, service: str, environment: str) -> bool:
        """
        Switch both service and environment.

        Returns:
            True if successful, False if invalid
        """
        service_obj = self.config.get_service(service)
        if not service_obj:
            return False

        if environment not in service_obj.environments:
            return False

        self.current_service = service_obj.name
        self.current_environment = environment
        return True

    def get_current_context(self) -> tuple[Optional[str], str]:
        """Get current service and environment."""
        return self.current_service, self.current_environment

    def get_base_url(
        self, service: Optional[str] = None, environment: Optional[str] = None
    ) -> Optional[str]:
        """Get base URL for service and environment."""
        service = service or self.current_service
        environment = environment or self.current_environment

        if not service:
            return None

        service_obj = self.config.get_service(service)
        if not service_obj:
            return None

        env_config = service_obj.environments.get(environment)
        if not env_config:
            return None

        return env_config.base_url

    def get_headers(
        self,
        service: Optional[str] = None,
        environment: Optional[str] = None,
        additional_headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, str]:
        """Get headers for current or specified context."""
        service = service or self.current_service
        environment = environment or self.current_environment

        if not service or not environment:
            return {}

        return self.header_manager.get_headers(service, environment, additional_headers)

    def get_certificates(self, environment: Optional[str] = None) -> Optional[Certificates]:
        """Get certificates for environment."""
        environment = environment or self.current_environment
        return self.config.get_certificates(environment)

    def resolve_url(
        self,
        input_str: str,
        default_service: Optional[str] = None,
        default_env: Optional[str] = None,
    ) -> tuple[RequestSpec, str]:
        """
        Parse input and resolve to full URL.

        Returns:
            Tuple of (RequestSpec, full_url)
        """
        default_service = default_service or self.current_service
        default_env = default_env or self.current_environment

        spec = self.url_resolver.parse(input_str, default_service, default_env)
        url = self.url_resolver.resolve(spec)

        return spec, url

    def list_services(self) -> list[str]:
        """Get list of all configured services."""
        return self.config.list_services()

    def list_environments(self, service: Optional[str] = None) -> list[str]:
        """Get list of environments for service or all environments."""
        service = service or self.current_service
        return self.config.list_environments(service)

    def get_service_info(self, service: Optional[str] = None) -> Optional[Dict]:
        """Get information about a service."""
        service = service or self.current_service
        if not service:
            return None

        service_obj = self.config.get_service(service)
        if not service_obj:
            return None

        return {
            "name": service_obj.name,
            "description": service_obj.description,
            "environments": list(service_obj.environments.keys()),
            "aliases": service_obj.aliases,
        }

    def get_environment_info(
        self, environment: Optional[str] = None, service: Optional[str] = None
    ) -> Optional[Dict]:
        """Get information about an environment."""
        service = service or self.current_service
        environment = environment or self.current_environment

        if not service or not environment:
            return None

        service_obj = self.config.get_service(service)
        if not service_obj:
            return None

        env_config = service_obj.environments.get(environment)
        if not env_config:
            return None

        return {
            "name": environment,
            "base_url": env_config.base_url,
            "timeout": env_config.timeout,
            "verify_ssl": env_config.verify_ssl,
        }

    def set_header(self, name: str, value: str):
        """Set a session header."""
        self.header_manager.set_session_header(name, value)

    def unset_header(self, name: str):
        """Remove a session header."""
        self.header_manager.unset_session_header(name)

    def clear_headers(self):
        """Clear all session headers."""
        self.header_manager.clear_session_headers()

    def set_variable(self, name: str, value: str):
        """Set a variable value."""
        self.header_manager.set_variable(name, value)

    def get_variable(self, name: str) -> Optional[str]:
        """Get a variable value."""
        return self.header_manager.get_variable(name)

    def list_variables(self) -> Dict[str, str]:
        """Get all variables."""
        return self.header_manager.list_variables()

    def get_prompt_string(self) -> str:
        """Get formatted prompt string for REPL."""
        if self.current_service and self.current_environment:
            return f"nodi [{self.current_service}.{self.current_environment}]> "
        elif self.current_service:
            return f"nodi [{self.current_service}]> "
        else:
            return "nodi> "
