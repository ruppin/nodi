"""REPL interface for Nodi."""

import re
import sys
from typing import Optional
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
from nodi.utils.color import Color


class NodiREPL:
    """Interactive REPL for Nodi."""

    def __init__(self, config: Config):
        self.config = config
        self.env_manager = EnvironmentManager(config)
        self.rest_provider = RestProvider()
        self.history = HistoryManager()
        self.json_filter = JSONFilter()

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
        # Check for filter first (preserve the full command with |)
        filter_expr = None
        if "|" in command:
            # Split on first | to get command and filter
            cmd_part, filter_part = command.split("|", 1)
            command = cmd_part.strip()
            # Remove 'jq' keyword if present
            filter_expr = filter_part.strip()
            if filter_expr.startswith("jq "):
                filter_expr = filter_expr[3:].strip()

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

        elif cmd == "history":
            self._show_history(parts)

        elif cmd == "clear":
            print("\033[2J\033[H")  # Clear screen

        elif cmd == "format":
            self._handle_format(parts)

        elif cmd in ("get", "post", "put", "patch", "delete", "head", "options"):
            self._handle_http_request(cmd.upper(), parts[1:], filter_expr)

        else:
            # Try as endpoint request (GET by default)
            self._handle_http_request("GET", parts, filter_expr)

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

    def _handle_http_request(self, method: str, args: list, filter_expr: Optional[str] = None):
        """Handle HTTP request."""
        if not args:
            print(f"Usage: {method.lower()} <endpoint> [-H <header>] [params...]")
            return

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

            # Display response
            self._display_response(response, filter_expr)

        except Exception as e:
            print(Color.error(f"Request failed: {str(e)}"))

    def _display_response(self, response, filter_expr: Optional[str] = None):
        """Display response."""
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

        # Apply filter if specified
        data = response.data
        if filter_expr and data:
            try:
                data = self.json_filter.apply(data, filter_expr)
            except Exception as e:
                print(Color.warning(f"Filter error: {str(e)}"))

        # Format output
        if data is not None:
            print()
            if self.output_format == "json":
                print(self.json_formatter.format(data))
            elif self.output_format == "yaml":
                print(self.yaml_formatter.format(data))
            elif self.output_format == "table":
                print(self.table_formatter.format(data))
