"""Provider manager for registering and managing data providers."""

from typing import Dict, Optional, Type
from nodi.providers.base import DataProvider


class ProviderManager:
    """Manages data providers."""

    def __init__(self):
        self._providers: Dict[str, DataProvider] = {}
        self._provider_types: Dict[str, Type[DataProvider]] = {}

    def register_provider_type(self, name: str, provider_class: Type[DataProvider]):
        """
        Register a provider type.

        Args:
            name: Provider type name (e.g., 'rest', 'mongodb')
            provider_class: Provider class
        """
        self._provider_types[name] = provider_class

    def create_provider(
        self, name: str, provider_type: str, config: Optional[Dict] = None
    ) -> DataProvider:
        """
        Create and register a provider instance.

        Args:
            name: Instance name
            provider_type: Type of provider
            config: Provider configuration

        Returns:
            Created provider instance
        """
        if provider_type not in self._provider_types:
            raise ValueError(f"Unknown provider type: {provider_type}")

        provider_class = self._provider_types[provider_type]
        provider = provider_class(name=name, config=config)
        self._providers[name] = provider

        return provider

    def get_provider(self, name: str) -> Optional[DataProvider]:
        """Get a provider by name."""
        return self._providers.get(name)

    def remove_provider(self, name: str) -> bool:
        """
        Remove and close a provider.

        Returns:
            True if removed, False if not found
        """
        if name in self._providers:
            provider = self._providers[name]
            provider.close()
            del self._providers[name]
            return True
        return False

    def list_providers(self) -> Dict[str, str]:
        """
        List all registered providers.

        Returns:
            Dict mapping provider name to provider type
        """
        return {name: provider.__class__.__name__ for name, provider in self._providers.items()}

    def list_provider_types(self) -> list[str]:
        """List all registered provider types."""
        return list(self._provider_types.keys())

    def close_all(self):
        """Close all providers."""
        for provider in self._providers.values():
            provider.close()
        self._providers.clear()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close_all()
