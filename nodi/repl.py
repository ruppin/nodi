"""REPL interface for Nodi."""

import re
import sys
from typing import Optional, Any
from prompt_toolkit import PromptSession
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.history import FileHistory
from pathlib import Path

from nodi.config.models import Config
from nodi.config.loader import ConfigLoader
from nodi.environment.manager import EnvironmentManager
from nodi.providers.rest import RestProvider
from nodi.providers.base import ProviderRequest
from nodi.formatters.json import JSONFormatter
from nodi.formatters.yaml_fmt import YAMLFormatter
from nodi.formatters.table import TableFormatter
from nodi.history import HistoryManager
from nodi.filters import JSONFilter
from nodi.projections import JSONProjection
from nodi.scripting import ScriptEngine, SuiteRunner
from nodi.utils.color import Color
import glob
import os


class NodiREPL:
    """Interactive REPL for Nodi."""

    def __init__(self, config: Config):
        self.config = config
        self.env_manager = EnvironmentManager(config)
        self.rest_provider = RestProvider()
        self.history = HistoryManager()
        self.json_filter = JSONFilter()
        self.json_projection = JSONProjection()

        # Scripting
        self.script_engine = ScriptEngine(
            config=config,
            rest_provider=self.rest_provider,
            resolver=self.env_manager.resolver
        )
        self.suite_runner = SuiteRunner(self.script_engine)

        # Formatters
        self.json_formatter = JSONFormatter(colored=True)
        self.yaml_formatter = YAMLFormatter()
        self.table_formatter = TableFormatter()

        # REPL session
        history_file = Path.home() / ".nodi" / "repl_history"
        history_file.parent.mkdir(parents=True, exist_ok=True)

        self.session = PromptSession(
            history=FileHistory(str(history_file)),
            auto_suggest=AutoSuggestFromHistory(),
        )

        # Current output format
        self.output_format = "json"  # json, yaml, table

    def run(self):
        """Run the REPL."""
        self._print_welcome()

        while True:
            try:
                # Get prompt
                prompt = self.env_manager.get_prompt_string()

                # Get input
                user_input = self.session.prompt(
                    prompt,
                    completer=self._get_completer(),
                )

                # Process command
                if not user_input.strip():
                    continue

                self._process_command(user_input.strip())

            except KeyboardInterrupt:
                continue
            except EOFError:
                print("\nGoodbye!")
                break
            except Exception as e:
                print(Color.error(f"Error: {str(e)}"))

    def _print_welcome(self):
        """Print welcome message."""
        print(Color.bold("Nodi - Interactive Data Query Tool"))
        print("Type 'help' for available commands, 'exit' to quit\n")

        # Show current context
        service, env = self.env_manager.get_current_context()
        if service and env:
            print(f"Current context: {Color.info(f'{service}.{env}')}\n")

    def _get_completer(self) -> WordCompleter:
        """Get command completer."""
        commands = [
            "help",
            "exit",
            "quit",
            "services",
            "envs",
            "use",
            "service",
            "env",
            "headers",
            "set-header",
            "unset-header",
            "variables",
            "set-variable",
            "get-variable",
            "history",
            "clear",
            "get",
            "post",
            "put",
            "patch",
            "delete",
            "format",
            "run",
            "run-suite",
            "scripts",
            "show",
        ]

        # Add service names
        commands.extend(self.env_manager.list_services())

        # Add aliases for current service
        service_info = self.env_manager.get_service_info()
        if service_info:
            commands.extend(service_info["aliases"].keys())

        return WordCompleter(commands, ignore_case=True)

    def _process_command(self, command: str):
        """Process a REPL command."""
        # Check for filter/projection chain (split on ALL pipes, not just first one)
        filter_chain = []

        if "|" in command:
            # Split on ALL pipes to support chaining: users | @filter1 | @filter2 | %projection
            pipe_parts = command.split("|")
            command = pipe_parts[0].strip()

            # Process all filter/projection parts
            for filter_part in pipe_parts[1:]:
                filter_part = filter_part.strip()

                # Remove 'jq' keyword if present
                if filter_part.startswith("jq "):
                    filter_part = filter_part[3:].strip()

                if filter_part:
                    filter_chain.append(filter_part)

        parts = command.split()
        if not parts:
            return

        cmd = parts[0].lower()

        # Commands
        if cmd in ("exit", "quit"):
            print("Goodbye!")
            sys.exit(0)

        elif cmd == "help":
            self._show_help()

        elif cmd == "services":
            self._show_services()

        elif cmd == "envs":
            self._show_environments()

        elif cmd == "use":
            self._handle_use(parts)

        elif cmd == "service":
            self._handle_service(parts)

        elif cmd == "env":
            self._handle_env(parts)

        elif cmd == "headers":
            self._show_headers()

        elif cmd == "set-header":
            self._handle_set_header(parts)

        elif cmd == "unset-header":
            self._handle_unset_header(parts)

        elif cmd == "variables":
            self._show_variables()

        elif cmd == "set-variable":
            self._handle_set_variable(parts)

        elif cmd == "get-variable":
            self._handle_get_variable(parts)

        elif cmd == "filters":
            self._show_filters()

        elif cmd == "projections":
            self._show_projections()

        elif cmd == "run":
            self._handle_run_script(parts)

        elif cmd == "run-suite":
            self._handle_run_suite(parts)

        elif cmd == "scripts":
            self._show_scripts()

        elif cmd == "show":
            self._handle_show_script(parts)

        elif cmd == "history":
            self._show_history(parts)

        elif cmd == "clear":
            print("\033[2J\033[H")  # Clear screen

        elif cmd == "format":
            self._handle_format(parts)

        elif cmd in ("get", "post", "put", "patch", "delete", "head", "options"):
            self._handle_http_request(cmd.upper(), parts[1:], filter_chain)

        else:
            # Try as endpoint request (GET by default)
            self._handle_http_request("GET", parts, filter_chain)

    def _show_help(self):
        """Show help message."""
        help_text = """
Available commands:

Service/Environment Management:
  services              List all services
  envs                  List environments
  use <service>.<env>   Switch service and environment
  service <name>        Switch to service
  env <name>            Switch to environment

Requests:
  get <endpoint>        GET request
  post <endpoint>       POST request
  put <endpoint>        PUT request
  patch <endpoint>      PATCH request
  delete <endpoint>     DELETE request

  Options:
    -H <header>          Add/override header with variable substitution
                         Format: -H "Name:Value" or -H Name:$variable

  Examples:
    users                      # GET current service's users alias
    user:123                   # GET user with ID 123
    users | jq length          # GET with jq filter
    users | .name              # Filter without 'jq' keyword
    search q=john status=active  # GET with query params
    post users {"name": "John"}  # POST with JSON body
    get users -H Cookie:$auth_cookie2  # Override cookie with variable
    get profile -H Authorization:Bearer_$token  # Override auth header

Headers:
  headers               Show current headers
  set-header <name> <value>   Set session header
  unset-header <name>   Remove session header

Variables:
  variables             Show all variables
  set-variable <name> <value>  Set variable value
  get-variable <name>   Get variable value

Filters:
  filters               Show predefined filters
  users | @filter_name  Apply predefined filter by name
  users | @emails       Example: Extract all emails
  users | .[*].id       Direct filter expression (without @)

Projections:
  projections           Show predefined projections
  users | %projection   Apply predefined projection (field selection)
  users | %user_summary Example: Show only id, name, email

Chaining (NEW):
  users | @active | %summary | .[0]     Chain filters and projections
  users | .[] | .name | jq length       Multiple transformations in sequence
  users | %basic | @verified            Projection then filter

Scripts:
  scripts               List all .nodi script files
  show <script>         Show script content
  run <script> [params] Run a single script with optional named parameters
  run <script1> <script2> ...  Run multiple scripts sequentially
  run --parallel <scripts...>  Run multiple scripts in parallel
  run-suite <suite.yml> Run a test suite

  Examples:
    run test_login.nodi user_id=123 token=abc
    run test_*.nodi
    run --parallel load_test1.nodi load_test2.nodi
    run-suite integration_tests.yml

Output:
  format <json|yaml|table>    Set output format

History:
  history               Show request history
  history clear         Clear history

Other:
  clear                 Clear screen
  help                  Show this help
  exit, quit            Exit REPL
"""
        print(help_text)

    def _show_services(self):
        """List all services."""
        services = self.env_manager.list_services()
        if not services:
            print("No services configured")
            return

        print(Color.bold("Available services:"))
        for service_name in services:
            service_info = self.env_manager.get_service_info(service_name)
            envs = ", ".join(service_info["environments"])
            print(f"  {Color.info(service_name):30s} → {envs}")

    def _show_environments(self):
        """List environments."""
        service, current_env = self.env_manager.get_current_context()

        if service:
            envs = self.env_manager.list_environments(service)
            print(Color.bold(f"Environments for {service}:"))
            for env in envs:
                marker = "→" if env == current_env else " "
                print(f"  {marker} {env}")
        else:
            print("No service selected")

    def _handle_use(self, parts):
        """Handle 'use' command."""
        if len(parts) < 2:
            print("Usage: use <service>.<environment>")
            return

        spec = parts[1]
        if "." not in spec:
            print("Format: use <service>.<environment>")
            return

        service, env = spec.split(".", 1)

        if self.env_manager.switch_context(service, env):
            print(f"Switched to {Color.info(f'{service}.{env}')}")
            base_url = self.env_manager.get_base_url()
            print(f"Base URL: {base_url}")
        else:
            print(Color.error(f"Invalid service or environment: {spec}"))

    def _handle_service(self, parts):
        """Handle 'service' command."""
        if len(parts) < 2:
            # Show current service info
            info = self.env_manager.get_service_info()
            if info:
                print(Color.bold(f"Service: {info['name']}"))
                if info['description']:
                    print(f"Description: {info['description']}")
                print(f"Environments: {', '.join(info['environments'])}")
                print(f"Aliases: {len(info['aliases'])}")
            return

        service_name = parts[1]
        if self.env_manager.switch_service(service_name):
            print(f"Switched to service: {Color.info(service_name)}")
        else:
            print(Color.error(f"Service not found: {service_name}"))

    def _handle_env(self, parts):
        """Handle 'env' command."""
        if len(parts) < 2:
            # Show current environment
            info = self.env_manager.get_environment_info()
            if info:
                print(Color.bold(f"Environment: {info['name']}"))
                print(f"Base URL: {info['base_url']}")
                print(f"Timeout: {info['timeout']}s")
                print(f"Verify SSL: {info['verify_ssl']}")
            return

        env_name = parts[1]
        if self.env_manager.switch_environment(env_name):
            print(f"Switched to environment: {Color.info(env_name)}")
        else:
            print(Color.error(f"Environment not found: {env_name}"))

    def _show_headers(self):
        """Show current headers."""
        service, env = self.env_manager.get_current_context()
        if not service or not env:
            print("No service/environment selected")
            return

        headers = self.env_manager.get_headers()
        masked_headers = self.env_manager.header_manager.mask_sensitive_headers(headers)

        print(Color.bold(f"Headers for {service}.{env}:"))
        for name, value in masked_headers.items():
            print(f"  {name}: {value}")

    def _handle_set_header(self, parts):
        """Handle set-header command."""
        if len(parts) < 3:
            print("Usage: set-header <name> <value>")
            return

        name = parts[1]
        value = " ".join(parts[2:])
        self.env_manager.set_header(name, value)
        print(f"Set header: {Color.info(name)}")

    def _handle_unset_header(self, parts):
        """Handle unset-header command."""
        if len(parts) < 2:
            print("Usage: unset-header <name>")
            return

        name = parts[1]
        self.env_manager.unset_header(name)
        print(f"Removed header: {Color.info(name)}")

    def _show_variables(self):
        """Show all variables."""
        variables = self.env_manager.list_variables()

        if not variables:
            print("No variables configured")
            return

        print(Color.bold("Variables:"))
        for name, value in variables.items():
            # Mask sensitive-looking values
            if any(word in name.lower() for word in ['cookie', 'token', 'password', 'secret', 'key']):
                if len(value) > 10:
                    masked_value = f"{value[:3]}***{value[-3:]}"
                else:
                    masked_value = "***"
                print(f"  {Color.info(name):30s} → {masked_value}")
            else:
                print(f"  {Color.info(name):30s} → {value}")

    def _handle_set_variable(self, parts):
        """Handle set-variable command."""
        if len(parts) < 3:
            print("Usage: set-variable <name> <value>")
            return

        name = parts[1]
        value = " ".join(parts[2:])
        self.env_manager.set_variable(name, value)
        print(f"Set variable: {Color.info(name)}")

    def _handle_get_variable(self, parts):
        """Handle get-variable command."""
        if len(parts) < 2:
            print("Usage: get-variable <name>")
            return

        name = parts[1]
        value = self.env_manager.get_variable(name)
        if value is not None:
            # Mask sensitive values
            if any(word in name.lower() for word in ['cookie', 'token', 'password', 'secret', 'key']):
                if len(value) > 10:
                    masked_value = f"{value[:3]}***{value[-3:]}"
                else:
                    masked_value = "***"
                print(f"{Color.info(name)}: {masked_value}")
            else:
                print(f"{Color.info(name)}: {value}")
        else:
            print(Color.warning(f"Variable not found: {name}"))

    def _substitute_variables_in_string(self, value: str) -> str:
        """
        Substitute variable references in a string.
        Supports both $variable_name and ${variable_name} syntax.
        """
        # Pattern for $variable_name or ${variable_name}
        pattern = re.compile(r'\$\{?(\w+)\}?')

        def replace(match):
            var_name = match.group(1)
            var_value = self.env_manager.get_variable(var_name)
            if var_value is not None:
                return var_value
            else:
                # Return original if variable not found
                return match.group(0)

        return pattern.sub(replace, value)

    def _show_filters(self):
        """Show all predefined filters."""
        filters = self.env_manager.config.list_filters()
        if filters:
            print(f"\n{Color.BOLD}Predefined Filters:{Color.RESET}")
            for name, expression in filters.items():
                print(f"  {Color.info(f'@{name}')}: {expression}")
            print(f"\n{Color.DIM}Use: endpoint | @filter_name{Color.RESET}")
        else:
            print("No predefined filters configured")

    def _show_projections(self):
        """Show all predefined projections."""
        projections = self.env_manager.config.list_projections()
        if projections:
            print(f"\n{Color.BOLD}Predefined Projections:{Color.RESET}")
            for name, spec in projections.items():
                import json
                spec_str = json.dumps(spec) if isinstance(spec, (list, dict)) else str(spec)
                print(f"  {Color.info(f'%{name}')}: {spec_str}")
            print(f"\n{Color.DIM}Use: endpoint | %projection_name{Color.RESET}")
        else:
            print("No predefined projections configured")

    def _resolve_filter(self, filter_expr: str) -> str:
        """
        Resolve predefined filter names to their expressions.
        Supports both @filter_name and filter_name syntax.

        Args:
            filter_expr: Filter expression (may be a filter name or actual expression)

        Returns:
            Resolved filter expression
        """
        if not filter_expr:
            return filter_expr

        # Check if it's a predefined filter reference (@filter_name)
        if filter_expr.startswith("@"):
            filter_name = filter_expr[1:].strip()
            predefined_filter = self.env_manager.config.get_filter(filter_name)
            if predefined_filter:
                return predefined_filter
            else:
                # Filter name not found, return original (will likely fail, but let user know)
                print(Color.warning(f"Warning: Predefined filter '@{filter_name}' not found. Using as literal expression."))
                return filter_expr

        # Not a filter reference, return as-is
        return filter_expr

    def _resolve_projection(self, projection_name: str) -> Optional[Any]:
        """
        Resolve predefined projection name to its specification.

        Args:
            projection_name: Projection name (without %)

        Returns:
            Projection specification or None if not found
        """
        if not projection_name:
            return None

        predefined_projection = self.env_manager.config.get_projection(projection_name)
        if predefined_projection:
            return predefined_projection
        else:
            # Projection name not found
            print(Color.warning(f"Warning: Predefined projection '%{projection_name}' not found."))
            return None

    def _show_history(self, parts):
        """Show request history."""
        if len(parts) > 1 and parts[1] == "clear":
            self.history.clear()
            print("History cleared")
            return

        recent = self.history.get_recent(20)
        print(self.history.format_entries(recent))

    def _handle_format(self, parts):
        """Handle format command."""
        if len(parts) < 2:
            print(f"Current format: {Color.info(self.output_format)}")
            print("Available formats: json, yaml, table")
            return

        fmt = parts[1].lower()
        if fmt in ("json", "yaml", "table"):
            self.output_format = fmt
            print(f"Output format set to: {Color.info(fmt)}")
        else:
            print(Color.error(f"Invalid format: {fmt}"))

    def _handle_http_request(self, method: str, args: list, filter_chain: list = None):
        """Handle HTTP request with support for chained filters and projections."""
        if not args:
            print(f"Usage: {method.lower()} <endpoint> [-H <header>] [params...]")
            return

        if filter_chain is None:
            filter_chain = []

        # Parse arguments
        endpoint_spec = args[0]
        additional_headers = {}

        # Parse -H flags
        i = 1
        while i < len(args):
            if args[i] == '-H' and i + 1 < len(args):
                # Parse header in format "Name:Value" or "Name: Value"
                header_str = args[i + 1]
                if ':' in header_str:
                    name, value = header_str.split(':', 1)
                    name = name.strip()
                    value = value.strip()

                    # Substitute variables in the value
                    value = self._substitute_variables_in_string(value)
                    additional_headers[name] = value
                i += 2
            else:
                i += 1

        try:
            # Resolve URL
            spec, url = self.env_manager.resolve_url(endpoint_spec)

            # Get headers (with additional headers that override defaults)
            headers = self.env_manager.get_headers()
            headers.update(additional_headers)

            # Get certificates for the current environment
            certificates = self.env_manager.get_certificates()

            # Create request
            request = ProviderRequest(
                method=method,
                resource=url,
                headers=headers,
            )

            # Execute request with certificates
            response = self.rest_provider.request(request, certificates=certificates)

            # Add to history
            self.history.add(
                method=method,
                service=spec.service,
                environment=spec.environment,
                url=url,
                status_code=response.status_code,
                elapsed_ms=response.elapsed_time or 0,
            )

            # Display response with filter chain
            self._display_response(response, filter_chain)

        except Exception as e:
            print(Color.error(f"Request failed: {str(e)}"))

    def _display_response(self, response, filter_chain: list = None):
        """Display response with support for chained filters and projections."""
        # Show status
        if response.is_success:
            status_color = Color.GREEN
        elif response.is_error:
            status_color = Color.RED
        else:
            status_color = Color.YELLOW

        print(
            Color.colorize(
                f"Status: {response.status_code} ({response.elapsed_time:.0f}ms)",
                status_color,
            )
        )

        # Start with response data
        data = response.data

        # Apply all filters and projections in the chain sequentially
        # This matches the behavior in engine.py (lines 154-180)
        if filter_chain and data:
            for filter_spec in filter_chain:
                filter_spec = filter_spec.strip()

                try:
                    if filter_spec.startswith('%'):
                        # Projection
                        projection_name = filter_spec[1:].strip()
                        projection_spec = self._resolve_projection(projection_name)
                        if projection_spec:
                            data = self.json_projection.apply(data, projection_spec)
                        else:
                            print(Color.warning(f"Unknown projection: %{projection_name}"))

                    elif filter_spec.startswith('@'):
                        # Predefined filter
                        filter_name = filter_spec[1:].strip()
                        filter_expr = self._resolve_filter(filter_spec)
                        if filter_expr and filter_expr != filter_spec:
                            # Filter was resolved, apply it
                            data = self.json_filter.apply(data, filter_expr)
                        else:
                            # Filter not found, but try to apply it anyway
                            data = self.json_filter.apply(data, filter_spec)

                    else:
                        # Direct filter expression
                        data = self.json_filter.apply(data, filter_spec)

                except Exception as e:
                    print(Color.warning(f"Filter/Projection error on '{filter_spec}': {str(e)}"))
                    # Continue with current data even if one filter fails

        # Format output
        if data is not None:
            print()
            if self.output_format == "json":
                print(self.json_formatter.format(data))
            elif self.output_format == "yaml":
                print(self.yaml_formatter.format(data))
            elif self.output_format == "table":
                print(self.table_formatter.format(data))

    def _show_scripts(self):
        """List all .nodi script files."""
        # Look in current directory and .nodi/scripts
        script_dirs = [
            Path.cwd(),
            Path.home() / ".nodi" / "scripts",
        ]

        scripts_found = []
        for script_dir in script_dirs:
            if script_dir.exists():
                for script_file in script_dir.glob("*.nodi"):
                    scripts_found.append(str(script_file))

        if not scripts_found:
            print("No .nodi script files found")
            print(f"Searched in: {', '.join(str(d) for d in script_dirs)}")
            return

        print(Color.bold("Available Scripts:"))
        for script_path in sorted(scripts_found):
            script_name = Path(script_path).name
            print(f"  {Color.info(script_name)} - {script_path}")

    def _handle_show_script(self, parts):
        """Show script content."""
        if len(parts) < 2:
            print(Color.error("Usage: show <script.nodi>"))
            return

        script_name = parts[1]
        script_path = self._find_script(script_name)

        if not script_path:
            print(Color.error(f"Script not found: {script_name}"))
            return

        print(Color.bold(f"Script: {script_name}"))
        print("-" * 70)

        with open(script_path, 'r', encoding='utf-8') as f:
            content = f.read()
            print(content)

    def _handle_run_script(self, parts):
        """Run one or more scripts."""
        if len(parts) < 2:
            print(Color.error("Usage: run <script.nodi> [params] or run --parallel <scripts...>"))
            return

        # Check for --parallel flag
        parallel = False
        if parts[1] == "--parallel":
            parallel = True
            parts = parts[1:]  # Remove --parallel from parts

        if len(parts) < 2:
            print(Color.error("No scripts specified"))
            return

        # Collect script paths and parameters
        script_paths = []
        params = {}

        for arg in parts[1:]:
            # Check if it's a parameter (key=value)
            if '=' in arg:
                key, value = arg.split('=', 1)
                params[key] = value
            elif '*' in arg or '?' in arg:
                # Glob pattern
                matched = glob.glob(arg)
                for match in matched:
                    if match.endswith('.nodi'):
                        script_paths.append(match)
            else:
                # Script name
                script_path = self._find_script(arg)
                if script_path:
                    script_paths.append(script_path)
                else:
                    print(Color.error(f"Script not found: {arg}"))
                    return

        if not script_paths:
            print(Color.error("No valid scripts found"))
            return

        # Run scripts
        if parallel:
            self._run_scripts_parallel(script_paths)
        else:
            self._run_scripts_sequential(script_paths, params)

    def _run_scripts_sequential(self, script_paths, params):
        """Run multiple scripts sequentially."""
        total = len(script_paths)
        print(f"Running {total} script(s) sequentially...")
        print("=" * 70)

        passed = 0
        failed = 0

        for i, script_path in enumerate(script_paths):
            script_name = Path(script_path).name
            print(f"\n[{i+1}/{total}] Running {Color.info(script_name)}...")

            try:
                result = self.script_engine.run_script(script_path, params)

                if result['status'] == 'PASS':
                    print(Color.success(f"PASS ({result['duration']:.2f}s)"))
                    passed += 1

                    # Show output
                    for line in result.get('output', []):
                        print(f"  {line}")
                else:
                    print(Color.error(f"FAIL ({result['duration']:.2f}s)"))
                    failed += 1

                    # Show error
                    if 'error' in result:
                        print(Color.error(f"  Error: {result['error']}"))

            except Exception as e:
                print(Color.error(f"FAIL - {str(e)}"))
                failed += 1

        print("\n" + "=" * 70)
        failed_text = Color.error(f'{failed} failed') if failed > 0 else '0 failed'
        print(f"Results: {Color.success(f'{passed} passed')}, {failed_text}")

    def _run_scripts_parallel(self, script_paths):
        """Run multiple scripts in parallel."""
        print(f"Running {len(script_paths)} script(s) in parallel...")
        print("=" * 70)

        results = self.suite_runner.run_scripts_parallel(script_paths)

        print()
        for script_result in results['scripts']:
            script_name = Path(script_result['script']).name
            status = script_result['status']
            duration = script_result['duration']

            if status == 'PASS':
                print(f"[{Color.success('✓')}] {script_name} ({duration:.2f}s)")
            else:
                print(f"[{Color.error('✗')}] {script_name}")
                if 'error' in script_result:
                    print(f"    {Color.error(script_result['error'])}")

        print("\n" + "=" * 70)
        passed = results['passed']
        failed = results['failed']
        duration = results['duration']
        failed_text = Color.error(f'{failed} failed') if failed > 0 else '0 failed'
        print(f"Results: {Color.success(f'{passed} passed')}, {failed_text} ({duration:.2f}s total)")

    def _handle_run_suite(self, parts):
        """Run a test suite."""
        if len(parts) < 2:
            print(Color.error("Usage: run-suite <suite.yml>"))
            return

        suite_file = parts[1]
        suite_path = self._find_file(suite_file, ['.yml', '.yaml'])

        if not suite_path:
            print(Color.error(f"Suite file not found: {suite_file}"))
            return

        print(f"Running suite: {Color.info(suite_file)}")
        print("=" * 70)

        try:
            results = self.suite_runner.run_suite(suite_path)

            print(f"\nSuite: {Color.bold(results['suite'])}")
            print("-" * 70)

            for step in results['steps']:
                step_name = step.get('step', step.get('group', 'Unnamed'))
                script = step['script']
                status = step['status']
                duration = step['duration']

                if status == 'PASS':
                    print(f"[{Color.success('PASS')}] {step_name}: {script} ({duration:.2f}s)")
                else:
                    print(f"[{Color.error('FAIL')}] {step_name}: {script}")
                    if 'error' in step:
                        print(f"       {Color.error(step['error'])}")

            print("\n" + "=" * 70)
            passed = results['passed']
            failed = results['failed']
            duration = results['duration']
            failed_text = Color.error(f'{failed} failed') if failed > 0 else '0 failed'
            print(f"Suite completed: {Color.success(f'{passed} passed')}, {failed_text} ({duration:.2f}s total)")

        except Exception as e:
            print(Color.error(f"Suite execution failed: {str(e)}"))

    def _find_script(self, script_name):
        """Find a script file by name."""
        return self._find_file(script_name, ['.nodi'])

    def _find_file(self, filename, extensions):
        """Find a file in common locations."""
        # Add extension if not present
        if not any(filename.endswith(ext) for ext in extensions):
            filename = filename + extensions[0]

        # Search locations
        search_paths = [
            Path(filename),  # Absolute or relative path
            Path.cwd() / filename,  # Current directory
            Path.home() / ".nodi" / "scripts" / filename,  # User scripts
        ]

        for path in search_paths:
            if path.exists() and path.is_file():
                return str(path)

        return None
