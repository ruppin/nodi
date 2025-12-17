"""Python script runner for Nodi.

Executes .py scripts with Nodi API injection and safety features.
"""

import sys
import time
import traceback
from pathlib import Path
from typing import Dict, Any, Optional, Set
import importlib.util
import signal
from contextlib import contextmanager

from .python_api import NodiPythonAPI


class ScriptTimeoutError(Exception):
    """Raised when script execution times out."""
    pass


class ScriptExecutionError(Exception):
    """Raised when script execution fails."""
    pass


class PythonScriptRunner:
    """Execute Python scripts with Nodi context injection."""

    # Whitelist of safe modules that scripts can import
    SAFE_MODULES: Set[str] = {
        # Built-in modules
        'json', 'datetime', 'time', 'math', 'random', 'collections',
        'itertools', 'functools', 're', 'string', 'decimal', 'fractions',
        'statistics', 'base64', 'hashlib', 'hmac', 'uuid', 'enum',

        # Data processing
        'csv', 'urllib.parse',

        # Type hints
        'typing', 'dataclasses',
    }

    # Blacklist of dangerous modules
    UNSAFE_MODULES: Set[str] = {
        'os', 'subprocess', 'sys', 'eval', 'exec', 'compile',
        '__import__', 'open', 'file', 'input', 'raw_input',
        'execfile', 'reload', 'builtins', '__builtins__',
    }

    def __init__(self, rest_provider, resolver, config,
                 allow_unsafe_imports: bool = False,
                 timeout: int = 300):
        """Initialize Python script runner.

        Args:
            rest_provider: RestProvider instance
            resolver: URLResolver instance
            config: Config instance
            allow_unsafe_imports: Allow importing unsafe modules (default: False)
            timeout: Script execution timeout in seconds (default: 300)
        """
        self.rest_provider = rest_provider
        self.resolver = resolver
        self.config = config
        self.allow_unsafe_imports = allow_unsafe_imports
        self.timeout = timeout

    def run_script(self, script_path: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Execute a Python script.

        Args:
            script_path: Path to .py script file
            params: Named parameters to pass to script

        Returns:
            Execution result with status, duration, and output

        Raises:
            ScriptExecutionError: If script execution fails
            ScriptTimeoutError: If script times out
        """
        start_time = time.time()

        # Load script
        path = Path(script_path)
        if not path.exists():
            raise ScriptExecutionError(f"Script file not found: {script_path}")

        if path.suffix != '.py':
            raise ScriptExecutionError(f"Not a Python script: {script_path}")

        # Initialize variables with parameters
        variables = params.copy() if params else {}

        # Create Nodi API
        nodi_api = NodiPythonAPI(
            self.rest_provider,
            self.resolver,
            self.config,
            variables
        )

        # Prepare execution namespace
        namespace = {
            'nodi': nodi_api,
            'client': nodi_api.client,
            '__name__': '__main__',
            '__file__': str(path.absolute()),
        }

        # Add script parameters as variables
        namespace.update(variables)

        # Capture output
        output = []
        original_print = print

        def captured_print(*args, **kwargs):
            """Capture print output."""
            # Convert to string
            message = ' '.join(str(arg) for arg in args)
            output.append(message)
            # Also print normally
            original_print(*args, **kwargs)

        # Execute script with timeout
        try:
            # Replace print
            import builtins
            builtins.print = captured_print

            # Load and execute script
            spec = importlib.util.spec_from_file_location("__main__", path)
            module = importlib.util.module_from_spec(spec)

            # Inject namespace
            module.__dict__.update(namespace)

            # Execute with timeout
            with self._timeout(self.timeout):
                spec.loader.exec_module(module)

            duration = time.time() - start_time

            return {
                'status': 'PASS',
                'duration': duration,
                'output': output,
                'script': script_path,
                'variables': nodi_api.vars
            }

        except ScriptTimeoutError:
            duration = time.time() - start_time
            return {
                'status': 'TIMEOUT',
                'duration': duration,
                'error': f"Script timed out after {self.timeout}s",
                'output': output,
                'script': script_path
            }

        except AssertionError as e:
            duration = time.time() - start_time
            return {
                'status': 'FAIL',
                'duration': duration,
                'error': f"Assertion failed: {str(e)}",
                'output': output,
                'script': script_path,
                'traceback': traceback.format_exc()
            }

        except Exception as e:
            duration = time.time() - start_time
            return {
                'status': 'ERROR',
                'duration': duration,
                'error': str(e),
                'output': output,
                'script': script_path,
                'traceback': traceback.format_exc()
            }

        finally:
            # Restore print
            builtins.print = original_print

    @contextmanager
    def _timeout(self, seconds: int):
        """Context manager for execution timeout.

        Args:
            seconds: Timeout in seconds
        """
        def timeout_handler(signum, frame):
            raise ScriptTimeoutError(f"Script execution timed out after {seconds}s")

        # Note: signal.alarm only works on Unix
        if hasattr(signal, 'SIGALRM'):
            # Unix-based systems
            old_handler = signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(seconds)
            try:
                yield
            finally:
                signal.alarm(0)
                signal.signal(signal.SIGALRM, old_handler)
        else:
            # Windows - use threading
            import threading

            timer = None
            timed_out = [False]

            def timeout_func():
                timed_out[0] = True
                # Can't raise exception from thread, will be checked after execution

            timer = threading.Timer(seconds, timeout_func)
            timer.start()

            try:
                yield
                if timed_out[0]:
                    raise ScriptTimeoutError(f"Script execution timed out after {seconds}s")
            finally:
                timer.cancel()

    def validate_imports(self, script_content: str) -> bool:
        """Validate that script only imports safe modules.

        Args:
            script_content: Script source code

        Returns:
            True if all imports are safe

        Raises:
            ScriptExecutionError: If unsafe imports detected
        """
        if self.allow_unsafe_imports:
            return True

        import ast

        try:
            tree = ast.parse(script_content)
        except SyntaxError as e:
            raise ScriptExecutionError(f"Syntax error in script: {e}")

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    module = alias.name.split('.')[0]
                    if module in self.UNSAFE_MODULES:
                        raise ScriptExecutionError(
                            f"Unsafe import detected: {module}. "
                            f"Use --allow-unsafe-imports to override."
                        )
                    if module not in self.SAFE_MODULES and not self.allow_unsafe_imports:
                        raise ScriptExecutionError(
                            f"Module '{module}' not in safe list. "
                            f"Add to SAFE_MODULES or use --allow-unsafe-imports."
                        )

            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    module = node.module.split('.')[0]
                    if module in self.UNSAFE_MODULES:
                        raise ScriptExecutionError(
                            f"Unsafe import detected: {module}. "
                            f"Use --allow-unsafe-imports to override."
                        )

        return True

    def get_script_info(self, script_path: str) -> Dict[str, Any]:
        """Get information about a script.

        Args:
            script_path: Path to script file

        Returns:
            Script metadata
        """
        path = Path(script_path)

        if not path.exists():
            return {'exists': False}

        # Read script
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Extract docstring
        import ast
        try:
            tree = ast.parse(content)
            docstring = ast.get_docstring(tree)
        except:
            docstring = None

        # Find functions
        functions = []
        try:
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    func_doc = ast.get_docstring(node)
                    functions.append({
                        'name': node.name,
                        'docstring': func_doc
                    })
        except:
            pass

        return {
            'exists': True,
            'path': str(path.absolute()),
            'size': path.stat().st_size,
            'docstring': docstring,
            'functions': functions,
            'lines': len(content.splitlines())
        }
