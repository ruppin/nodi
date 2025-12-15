"""Tests for configuration management."""

import pytest
from nodi.config.models import Config, Service, ServiceEnvironment
from nodi.config.validator import ConfigValidator


def test_service_environment_creation():
    """Test ServiceEnvironment creation."""
    env = ServiceEnvironment(base_url="https://api.example.com")
    assert env.base_url == "https://api.example.com"
    assert env.timeout == 30
    assert env.verify_ssl is True


def test_service_creation():
    """Test Service creation."""
    service = Service(
        name="test-service",
        environments={
            "dev": ServiceEnvironment(base_url="https://dev.example.com"),
            "prod": ServiceEnvironment(base_url="https://prod.example.com"),
        },
        aliases={"users": "/api/v1/users"},
    )

    assert service.name == "test-service"
    assert len(service.environments) == 2
    assert "users" in service.aliases


def test_config_get_service():
    """Test Config.get_service()."""
    service = Service(
        name="test-service",
        environments={"dev": ServiceEnvironment(base_url="https://dev.example.com")},
    )

    config = Config(
        services={"test-service": service},
        service_aliases={"ts": "test-service"},
    )

    # Direct lookup
    assert config.get_service("test-service") == service

    # Alias lookup
    assert config.get_service("ts") == service

    # Not found
    assert config.get_service("unknown") is None


def test_config_list_environments():
    """Test Config.list_environments()."""
    service = Service(
        name="test-service",
        environments={
            "dev": ServiceEnvironment(base_url="https://dev.example.com"),
            "qa": ServiceEnvironment(base_url="https://qa.example.com"),
            "prod": ServiceEnvironment(base_url="https://prod.example.com"),
        },
    )

    config = Config(services={"test-service": service})

    # All environments
    envs = config.list_environments()
    assert set(envs) == {"dev", "qa", "prod"}

    # Service-specific
    envs = config.list_environments("test-service")
    assert set(envs) == {"dev", "qa", "prod"}


def test_config_validator():
    """Test ConfigValidator."""
    validator = ConfigValidator()

    # Valid config
    service = Service(
        name="test-service",
        environments={"dev": ServiceEnvironment(base_url="https://dev.example.com")},
    )
    config = Config(services={"test-service": service}, default_environment="dev")

    assert validator.validate(config) is True
    assert len(validator.get_errors()) == 0


def test_config_validator_errors():
    """Test ConfigValidator error detection."""
    validator = ConfigValidator()

    # Empty services
    config = Config(services={})
    assert validator.validate(config) is False
    assert len(validator.get_errors()) > 0


def test_config_validator_invalid_url():
    """Test ConfigValidator detects invalid URLs."""
    validator = ConfigValidator()

    service = Service(
        name="test-service",
        environments={"dev": ServiceEnvironment(base_url="invalid-url")},
    )
    config = Config(services={"test-service": service})

    assert validator.validate(config) is False
    errors = validator.get_errors()
    assert any("http://" in error or "https://" in error for error in errors)
