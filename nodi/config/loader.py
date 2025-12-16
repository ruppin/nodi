"""Configuration file loader for Nodi."""

import os
import re
from pathlib import Path
from typing import Optional, Dict, Any
import yaml
from dotenv import load_dotenv

from nodi.config.models import (
    Config,
    Service,
    ServiceEnvironment,
    EnvironmentHeaders,
    Certificates,
)


class ConfigLoader:
    """Load and parse Nodi configuration files."""

    def __init__(self):
        self.env_var_pattern = re.compile(r"\$\{(\w+)\}")

    def load(self, config_path: Optional[str] = None) -> Config:
        """
        Load configuration from file hierarchy.

        Priority (highest to lowest):
        1. Provided config_path
        2. Current directory .nodi.yml
        3. Parent directories (up to git root)
        4. User config ~/.nodi/config.yml
        5. System config /etc/nodi/config.yml
        """
        config_files = self._find_config_files(config_path)

        # Load .env file if present
        load_dotenv()

        # Start with empty config
        merged_config = {}

        # Merge configs from lowest to highest priority
        for config_file in reversed(config_files):
            if config_file.exists():
                file_config = self._load_yaml(config_file)
                merged_config = self._merge_configs(merged_config, file_config)

        # Substitute environment variables
        merged_config = self._substitute_env_vars(merged_config)

        # Parse into Config object
        config = self._parse_config(merged_config)

        # Note: We do NOT substitute ${var:*} variables here
        # They are kept as-is and resolved at request time by HeaderManager
        # This allows runtime variable updates

        return config

    def _find_config_files(self, config_path: Optional[str] = None) -> list[Path]:
        """Find all config files in priority order."""
        config_files = []

        # 5. System config (lowest priority)
        if os.name != "nt":  # Unix-like systems
            system_config = Path("/etc/nodi/config.yml")
            config_files.append(system_config)

        # 4. User config
        user_config = Path.home() / ".nodi" / "config.yml"
        config_files.append(user_config)

        # 3. Parent directories (up to git root or home)
        current_dir = Path.cwd()
        while current_dir != current_dir.parent and current_dir != Path.home():
            dir_config = current_dir / ".nodi.yml"
            if dir_config not in config_files:
                config_files.append(dir_config)

            # Stop at git root
            if (current_dir / ".git").exists():
                break

            current_dir = current_dir.parent

        # 2. Current directory
        current_config = Path.cwd() / ".nodi.yml"
        if current_config not in config_files:
            config_files.append(current_config)

        # 1. Provided path (highest priority)
        if config_path:
            config_files.append(Path(config_path))

        return config_files

    def _load_yaml(self, path: Path) -> Dict[str, Any]:
        """Load YAML file."""
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
                return data if data else {}
        except Exception as e:
            print(f"Warning: Failed to load config from {path}: {e}")
            return {}

    def _merge_configs(self, base: Dict, override: Dict) -> Dict:
        """Merge two config dictionaries recursively."""
        result = base.copy()

        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_configs(result[key], value)
            else:
                result[key] = value

        return result

    def _substitute_env_vars(self, config: Any) -> Any:
        """Recursively substitute environment variables in config."""
        if isinstance(config, dict):
            return {k: self._substitute_env_vars(v) for k, v in config.items()}
        elif isinstance(config, list):
            return [self._substitute_env_vars(item) for item in config]
        elif isinstance(config, str):
            return self._substitute_env_var_string(config)
        else:
            return config

    def _substitute_env_var_string(self, value: str) -> str:
        """Substitute environment variables in a string."""

        def replace(match):
            var_name = match.group(1)
            return os.environ.get(var_name, match.group(0))

        return self.env_var_pattern.sub(replace, value)

    def _parse_config(self, data: Dict[str, Any]) -> Config:
        """Parse config dictionary into Config object."""
        services = {}
        headers = {}
        certificates = {}

        # Parse services
        for service_name, service_data in data.get("services", {}).items():
            environments = {}
            aliases = service_data.get("aliases", {})

            # Parse environments for this service
            for env_name, env_data in service_data.items():
                if env_name == "aliases" or not isinstance(env_data, dict):
                    continue

                if "base_url" not in env_data:
                    continue

                environments[env_name] = ServiceEnvironment(
                    base_url=env_data["base_url"],
                    headers=env_data.get("headers"),
                    timeout=env_data.get("timeout", 30),
                    verify_ssl=env_data.get("verify_ssl", True),
                )

            services[service_name] = Service(
                name=service_name,
                environments=environments,
                aliases=aliases,
                description=service_data.get("description"),
            )

        # Parse headers per environment
        for env_name, env_headers in data.get("headers", {}).items():
            headers[env_name] = EnvironmentHeaders(headers=env_headers or {})

        # Parse certificates per environment
        for env_name, cert_data in data.get("certificates", {}).items():
            certificates[env_name] = Certificates(
                cert=cert_data.get("cert"),
                key=cert_data.get("key"),
                ca=cert_data.get("ca"),
                verify=cert_data.get("verify", True),
                ssl_version=cert_data.get("ssl_version"),
            )

        return Config(
            services=services,
            headers=headers,
            certificates=certificates,
            default_environment=data.get("default_environment", "dev"),
            default_service=data.get("default_service"),
            service_aliases=data.get("service_aliases", {}),
            profiles=data.get("profiles", {}),
            variables=data.get("variables", {}),
            filters=data.get("filters", {}),
            projections=data.get("projections", {}),
        )

    def create_default_config(self, path: Optional[Path] = None) -> Path:
        """Create a default configuration file."""
        if path is None:
            path = Path.home() / ".nodi" / "config.yml"

        path.parent.mkdir(parents=True, exist_ok=True)

        default_config = {
            "services": {
                "example-service": {
                    "dev": {"base_url": "https://api.dev.example.com"},
                    "qa": {"base_url": "https://api.qa.example.com"},
                    "prod": {"base_url": "https://api.prod.example.com"},
                    "aliases": {
                        "users": "/api/v1/users",
                        "user": "/api/v1/users/{id}",
                        "health": "/health",
                    },
                }
            },
            "headers": {
                "dev": {"X-Environment": "development"},
                "qa": {"X-Environment": "qa"},
                "prod": {"X-Environment": "production"},
            },
            "default_environment": "dev",
            "default_service": "example-service",
        }

        with open(path, "w", encoding="utf-8") as f:
            yaml.dump(default_config, f, default_flow_style=False, sort_keys=False)

        return path
