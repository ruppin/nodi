"""Base plugin classes for Nodi."""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, List
from pathlib import Path
import importlib.util
import sys


class Plugin(ABC):
    """Base class for Nodi plugins.

    Plugins can hook into the request/response lifecycle and
    extend Nodi functionality.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize plugin.

        Args:
            config: Plugin configuration from config.yml
        """
        self.config = config or {}
        self.enabled = self.config.get('enabled', True)

    @property
    @abstractmethod
    def name(self) -> str:
        """Plugin name."""
        pass

    @property
    def version(self) -> str:
        """Plugin version."""
        return "1.0.0"

    @property
    def description(self) -> str:
        """Plugin description."""
        return ""

    def on_load(self):
        """Called when plugin is loaded."""
        pass

    def on_unload(self):
        """Called when plugin is unloaded."""
        pass

    def before_request(self, request: Any) -> Any:
        """Called before HTTP request is sent.

        Args:
            request: ProviderRequest object

        Returns:
            Modified request object
        """
        return request

    def after_response(self, response: Any) -> Any:
        """Called after HTTP response is received.

        Args:
            response: ProviderResponse object

        Returns:
            Modified response object
        """
        return response

    def on_error(self, error: Exception) -> Optional[Exception]:
        """Called when an error occurs.

        Args:
            error: Exception that occurred

        Returns:
            Modified exception or None to suppress
        """
        return error

    def transform_data(self, data: Any) -> Any:
        """Transform response data.

        Args:
            data: Response data

        Returns:
            Transformed data
        """
        return data


class PluginManager:
    """Manages plugin loading and lifecycle."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize plugin manager.

        Args:
            config: Configuration object
        """
        self.config = config or {}
        self.plugins: List[Plugin] = []
        self._plugin_paths: List[Path] = []

    def add_plugin_path(self, path: str):
        """Add directory to search for plugins.

        Args:
            path: Path to plugin directory
        """
        plugin_path = Path(path).expanduser()
        if plugin_path.exists() and plugin_path.is_dir():
            self._plugin_paths.append(plugin_path)
            # Add to Python path
            if str(plugin_path) not in sys.path:
                sys.path.insert(0, str(plugin_path))

    def load_plugin(self, plugin_class_or_path: str, config: Optional[Dict] = None) -> Optional[Plugin]:
        """Load a plugin.

        Args:
            plugin_class_or_path: Plugin class name (e.g., 'my_plugin.MyPlugin')
                                  or path to .py file
            config: Plugin configuration

        Returns:
            Loaded plugin instance or None
        """
        try:
            # Check if it's a file path
            if plugin_class_or_path.endswith('.py'):
                return self._load_plugin_from_file(plugin_class_or_path, config)
            else:
                return self._load_plugin_from_class(plugin_class_or_path, config)
        except Exception as e:
            print(f"Failed to load plugin '{plugin_class_or_path}': {e}")
            return None

    def _load_plugin_from_class(self, class_path: str, config: Optional[Dict] = None) -> Optional[Plugin]:
        """Load plugin from class path.

        Args:
            class_path: Full class path (e.g., 'my_plugin.MyPlugin')
            config: Plugin configuration

        Returns:
            Plugin instance or None
        """
        # Split module and class name
        parts = class_path.rsplit('.', 1)
        if len(parts) != 2:
            raise ValueError(f"Invalid plugin class path: {class_path}")

        module_name, class_name = parts

        # Import module
        try:
            module = importlib.import_module(module_name)
        except ImportError as e:
            # Try loading from plugin paths
            for plugin_path in self._plugin_paths:
                module_file = plugin_path / f"{module_name}.py"
                if module_file.exists():
                    spec = importlib.util.spec_from_file_location(module_name, module_file)
                    module = importlib.util.module_from_spec(spec)
                    sys.modules[module_name] = module
                    spec.loader.exec_module(module)
                    break
            else:
                raise ImportError(f"Cannot import module {module_name}: {e}")

        # Get plugin class
        if not hasattr(module, class_name):
            raise AttributeError(f"Module {module_name} has no class {class_name}")

        plugin_class = getattr(module, class_name)

        # Verify it's a Plugin subclass
        if not issubclass(plugin_class, Plugin):
            raise TypeError(f"{class_path} is not a Plugin subclass")

        # Instantiate plugin
        plugin = plugin_class(config)
        plugin.on_load()

        self.plugins.append(plugin)
        return plugin

    def _load_plugin_from_file(self, file_path: str, config: Optional[Dict] = None) -> Optional[Plugin]:
        """Load plugin from Python file.

        Args:
            file_path: Path to .py file
            config: Plugin configuration

        Returns:
            Plugin instance or None
        """
        path = Path(file_path).expanduser()
        if not path.exists():
            raise FileNotFoundError(f"Plugin file not found: {file_path}")

        # Load module
        module_name = path.stem
        spec = importlib.util.spec_from_file_location(module_name, path)
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)

        # Find Plugin subclass
        plugin_class = None
        for name in dir(module):
            obj = getattr(module, name)
            if isinstance(obj, type) and issubclass(obj, Plugin) and obj != Plugin:
                plugin_class = obj
                break

        if not plugin_class:
            raise ValueError(f"No Plugin subclass found in {file_path}")

        # Instantiate
        plugin = plugin_class(config)
        plugin.on_load()

        self.plugins.append(plugin)
        return plugin

    def load_plugins_from_config(self):
        """Load plugins defined in configuration."""
        plugin_configs = self.config.get('plugins', [])

        for plugin_config in plugin_configs:
            if isinstance(plugin_config, str):
                # Simple plugin name
                self.load_plugin(plugin_config)
            elif isinstance(plugin_config, dict):
                # Plugin with configuration
                name = plugin_config.get('name')
                config = plugin_config.get('config', {})
                if name:
                    self.load_plugin(name, config)

    def unload_plugin(self, plugin: Plugin):
        """Unload a plugin.

        Args:
            plugin: Plugin to unload
        """
        if plugin in self.plugins:
            plugin.on_unload()
            self.plugins.remove(plugin)

    def unload_all(self):
        """Unload all plugins."""
        for plugin in list(self.plugins):
            self.unload_plugin(plugin)

    def get_enabled_plugins(self) -> List[Plugin]:
        """Get list of enabled plugins.

        Returns:
            List of enabled plugins
        """
        return [p for p in self.plugins if p.enabled]

    def before_request(self, request: Any) -> Any:
        """Run before_request hook on all enabled plugins.

        Args:
            request: ProviderRequest object

        Returns:
            Modified request
        """
        for plugin in self.get_enabled_plugins():
            request = plugin.before_request(request)
        return request

    def after_response(self, response: Any) -> Any:
        """Run after_response hook on all enabled plugins.

        Args:
            response: ProviderResponse object

        Returns:
            Modified response
        """
        for plugin in self.get_enabled_plugins():
            response = plugin.after_response(response)
        return response

    def on_error(self, error: Exception) -> Optional[Exception]:
        """Run on_error hook on all enabled plugins.

        Args:
            error: Exception that occurred

        Returns:
            Modified exception or None
        """
        for plugin in self.get_enabled_plugins():
            error = plugin.on_error(error)
            if error is None:
                break
        return error

    def transform_data(self, data: Any) -> Any:
        """Run transform_data hook on all enabled plugins.

        Args:
            data: Response data

        Returns:
            Transformed data
        """
        for plugin in self.get_enabled_plugins():
            data = plugin.transform_data(data)
        return data

    def list_plugins(self) -> List[Dict[str, Any]]:
        """List all loaded plugins.

        Returns:
            List of plugin information
        """
        return [
            {
                'name': p.name,
                'version': p.version,
                'description': p.description,
                'enabled': p.enabled
            }
            for p in self.plugins
        ]
