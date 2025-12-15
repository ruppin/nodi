"""Configuration validator for Nodi."""

from typing import List, Optional
from nodi.config.models import Config, Service


class ConfigValidator:
    """Validate Nodi configuration."""

    def __init__(self):
        self.errors: List[str] = []
        self.warnings: List[str] = []

    def validate(self, config: Config) -> bool:
        """
        Validate configuration.

        Returns:
            True if valid, False if errors found
        """
        self.errors = []
        self.warnings = []

        self._validate_services(config)
        self._validate_defaults(config)
        self._validate_headers(config)
        self._validate_certificates(config)

        return len(self.errors) == 0

    def _validate_services(self, config: Config):
        """Validate service configurations."""
        if not config.services:
            self.errors.append("No services defined in configuration")
            return

        for service_name, service in config.services.items():
            if not service.environments:
                self.errors.append(f"Service '{service_name}' has no environments defined")
                continue

            # Validate each environment
            for env_name, env_config in service.environments.items():
                if not env_config.base_url:
                    self.errors.append(
                        f"Service '{service_name}' environment '{env_name}' has no base_url"
                    )

                if not env_config.base_url.startswith(("http://", "https://")):
                    self.errors.append(
                        f"Service '{service_name}' environment '{env_name}' "
                        f"base_url must start with http:// or https://"
                    )

            # Validate aliases
            for alias_name, alias_path in service.aliases.items():
                if not alias_path.startswith("/"):
                    self.warnings.append(
                        f"Service '{service_name}' alias '{alias_name}' "
                        f"should start with '/' (got: {alias_path})"
                    )

    def _validate_defaults(self, config: Config):
        """Validate default settings."""
        if config.default_service:
            service = config.get_service(config.default_service)
            if not service:
                self.errors.append(
                    f"Default service '{config.default_service}' not found in services"
                )
            elif config.default_environment not in service.environments:
                self.errors.append(
                    f"Default environment '{config.default_environment}' "
                    f"not found in default service '{config.default_service}'"
                )

    def _validate_headers(self, config: Config):
        """Validate header configurations."""
        # Check for potentially sensitive headers
        sensitive_patterns = ["password", "secret", "token", "key"]

        for env_name, env_headers in config.headers.items():
            for header_name, header_value in env_headers.headers.items():
                # Warn if sensitive value is not using env var
                if any(pattern in header_name.lower() for pattern in sensitive_patterns):
                    if not header_value.startswith("${"):
                        self.warnings.append(
                            f"Environment '{env_name}' header '{header_name}' "
                            f"contains sensitive data. Consider using environment variables."
                        )

    def _validate_certificates(self, config: Config):
        """Validate certificate configurations."""
        for env_name, certs in config.certificates.items():
            if certs.cert and not certs.key:
                self.errors.append(
                    f"Environment '{env_name}' has cert but no key specified"
                )
            if certs.key and not certs.cert:
                self.errors.append(
                    f"Environment '{env_name}' has key but no cert specified"
                )

    def get_errors(self) -> List[str]:
        """Get list of validation errors."""
        return self.errors

    def get_warnings(self) -> List[str]:
        """Get list of validation warnings."""
        return self.warnings

    def print_report(self):
        """Print validation report."""
        if self.errors:
            print("\nConfiguration Errors:")
            for error in self.errors:
                print(f"  ✗ {error}")

        if self.warnings:
            print("\nConfiguration Warnings:")
            for warning in self.warnings:
                print(f"  ⚠ {warning}")

        if not self.errors and not self.warnings:
            print("\n✓ Configuration is valid")
