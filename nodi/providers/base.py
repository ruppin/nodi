"""Base provider class for data sources."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, Optional
from datetime import datetime


@dataclass
class ProviderRequest:
    """Request specification for a data provider."""

    method: str  # GET, POST, etc. for REST; query type for DB
    resource: str  # URL for REST; collection/table for DB
    data: Optional[Any] = None
    headers: Optional[Dict[str, str]] = None
    params: Optional[Dict[str, str]] = None
    timeout: Optional[int] = 30
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ProviderResponse:
    """Response from a data provider."""

    status_code: int  # HTTP status or custom status code
    data: Any
    headers: Optional[Dict[str, str]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    elapsed_time: Optional[float] = None  # milliseconds
    timestamp: datetime = field(default_factory=datetime.now)

    @property
    def is_success(self) -> bool:
        """Check if response was successful."""
        return 200 <= self.status_code < 300

    @property
    def is_error(self) -> bool:
        """Check if response was an error."""
        return self.status_code >= 400


class DataProvider(ABC):
    """Abstract base class for data providers."""

    def __init__(self, name: str, config: Optional[Dict[str, Any]] = None):
        self.name = name
        self.config = config or {}

    @abstractmethod
    def request(self, request: ProviderRequest) -> ProviderResponse:
        """
        Execute a request and return response.

        Args:
            request: ProviderRequest with request details

        Returns:
            ProviderResponse with result
        """
        pass

    @abstractmethod
    def test_connection(self) -> bool:
        """
        Test if provider can connect to data source.

        Returns:
            True if connection successful, False otherwise
        """
        pass

    def close(self):
        """Close any open connections. Override if needed."""
        pass

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()

    def get_info(self) -> Dict[str, Any]:
        """Get provider information."""
        return {
            "name": self.name,
            "type": self.__class__.__name__,
            "config": self._get_safe_config(),
        }

    def _get_safe_config(self) -> Dict[str, Any]:
        """Get config with sensitive values masked."""
        safe_config = {}
        sensitive_keys = ["password", "token", "api_key", "secret", "apikey"]

        for key, value in self.config.items():
            if any(sensitive in key.lower() for sensitive in sensitive_keys):
                safe_config[key] = "***"
            else:
                safe_config[key] = value

        return safe_config
