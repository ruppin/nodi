"""Script execution engine for .nodi files."""

import re
import json
import time
from typing import Dict, Any, Optional, List
from pathlib import Path

from .parser import ScriptParser, ScriptLine
from ..config.models import Config
from ..providers.rest import RestProvider
from ..environment.resolver import URLResolver
from ..filters import JSONFilter
from ..projections import JSONProjection


class ScriptExecutionError(Exception):
    """Raised when script execution fails."""
    pass


class ScriptEngine:
    """Execute .nodi script files."""

    def __init__(self, config: Config, rest_provider: RestProvider,
                 resolver: URLResolver):
        self.config = config
        self.rest_provider = rest_provider
        self.resolver = resolver
        self.json_filter = JSONFilter()
        self.json_projection = JSONProjection()
        self.parser = ScriptParser()

        # Script-local variables (isolated from REPL)
        self.variables: Dict[str, Any] = {}
        self.last_response: Optional[Any] = None

    def run_script(self, script_path: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Execute a script file.

        Args:
            script_path: Path to .nodi script file
            params: Named parameters to pass to script

        Returns:
            Execution result with status, duration, and output
        """
        start_time = time.time()

        # Load script
        path = Path(script_path)
        if not path.exists():
            raise ScriptExecutionError(f"Script file not found: {script_path}")

        with open(path, 'r', encoding='utf-8') as f:
            script_content = f.read()

        # Initialize variables with parameters
        self.variables = params.copy() if params else {}
        self.last_response = None

        # Parse script
        parsed_lines = self.parser.parse(script_content)

        # Execute
        output = []
        try:
            for line in parsed_lines:
                result = self._execute_line(line)
                if result:
                    output.append(result)

            duration = time.time() - start_time
            return {
                'status': 'PASS',
                'duration': duration,
                'output': output,
                'script': script_path
            }

        except Exception as e:
            duration = time.time() - start_time
            return {
                'status': 'FAIL',
                'duration': duration,
                'error': str(e),
                'output': output,
                'script': script_path
            }

    def _execute_line(self, line: ScriptLine) -> Optional[str]:
        """Execute a single parsed line."""
        if line.line_type == 'comment' or line.line_type == 'unknown':
            return None

        elif line.line_type == 'assignment':
            return self._execute_assignment(line)

        elif line.line_type == 'http':
            return self._execute_http(line)

        elif line.line_type == 'assert':
            return self._execute_assert(line)

        elif line.line_type == 'print':
            return self._execute_print(line)

        elif line.line_type == 'echo':
            return self._execute_echo(line)

        elif line.line_type in ['if', 'for', 'end']:
            # TODO: Implement control flow in future version
            raise ScriptExecutionError(f"Control flow not yet implemented: {line.line_type}")

        return None

    def _execute_assignment(self, line: ScriptLine) -> str:
        """Execute variable assignment."""
        var_name = line.content['variable']
        expr = line.content['expression']

        # Evaluate expression
        value = self._evaluate_expression(expr)
        self.variables[var_name] = value

        return f"${var_name} = {json.dumps(value) if isinstance(value, (dict, list)) else value}"

    def _execute_http(self, line: ScriptLine) -> str:
        """Execute HTTP request."""
        method = line.content['method']
        endpoint = line.content['endpoint']
        filters = line.content.get('filters', [])

        # Substitute variables in endpoint
        endpoint = self._substitute_variables(endpoint)

        # Parse environment.service@endpoint syntax
        resolved = self.resolver.resolve(endpoint, method)

        # Make request
        response = self.rest_provider.request(
            method=resolved.method,
            url=resolved.url,
            headers=resolved.headers,
            params=resolved.params,
            json=resolved.body
        )

        # Store response
        self.last_response = response
        self.variables['response'] = response

        # Apply filters and projections
        result = response.get('data', response)
        for filter_spec in filters:
            filter_spec = filter_spec.strip()

            if filter_spec.startswith('%'):
                # Projection
                projection_name = filter_spec[1:]
                projection_spec = self.config.get_projection(projection_name)
                if projection_spec:
                    result = self.json_projection.apply(result, projection_spec)
                else:
                    raise ScriptExecutionError(f"Unknown projection: {projection_name}")

            elif filter_spec.startswith('@'):
                # Predefined filter
                filter_name = filter_spec[1:]
                filter_expr = self.config.get_filter(filter_name)
                if filter_expr:
                    result = self.json_filter.apply(result, filter_expr)
                else:
                    raise ScriptExecutionError(f"Unknown filter: {filter_name}")

            else:
                # Direct filter expression
                result = self.json_filter.apply(result, filter_spec)

        # Store filtered result
        self.variables['data'] = result

        status_code = response.get('status_code', 0)
        return f"{method} {endpoint} -> {status_code}"

    def _execute_assert(self, line: ScriptLine) -> str:
        """Execute assertion."""
        expr = line.content['expression']

        # Substitute variables
        expr = self._substitute_variables(expr)

        # Evaluate assertion
        result = self._evaluate_assertion(expr)

        if not result:
            raise ScriptExecutionError(f"Assertion failed at line {line.line_number}: {expr}")

        return f"assert {expr} -> OK"

    def _execute_print(self, line: ScriptLine) -> str:
        """Execute print statement."""
        expr = line.content['expression']

        # Evaluate expression
        value = self._evaluate_expression(expr)

        if isinstance(value, (dict, list)):
            return json.dumps(value, indent=2)
        else:
            return str(value)

    def _execute_echo(self, line: ScriptLine) -> str:
        """Execute echo statement."""
        message = line.content['message']

        # Substitute variables
        message = self._substitute_variables(message)

        return message

    def _substitute_variables(self, text: str) -> str:
        """Substitute $variable references in text."""
        pattern = re.compile(r'\$(\w+(?:\.\w+)*)')

        def replacer(match):
            var_path = match.group(1)
            parts = var_path.split('.')

            # Get root variable
            value = self.variables.get(parts[0])
            if value is None:
                return match.group(0)  # Keep as-is if not found

            # Navigate path
            for part in parts[1:]:
                if isinstance(value, dict):
                    value = value.get(part)
                elif isinstance(value, list) and part.isdigit():
                    idx = int(part)
                    value = value[idx] if 0 <= idx < len(value) else None
                else:
                    return match.group(0)

                if value is None:
                    return match.group(0)

            return str(value)

        return pattern.sub(replacer, text)

    def _evaluate_expression(self, expr: str) -> Any:
        """Evaluate an expression (variable reference or literal)."""
        expr = expr.strip()

        # Variable reference
        if expr.startswith('$'):
            var_path = expr[1:]
            parts = var_path.split('.')

            value = self.variables.get(parts[0])
            if value is None:
                return None

            for part in parts[1:]:
                if isinstance(value, dict):
                    value = value.get(part)
                elif isinstance(value, list) and part.isdigit():
                    idx = int(part)
                    value = value[idx] if 0 <= idx < len(value) else None
                else:
                    return None

            return value

        # Literal string (quoted)
        if (expr.startswith('"') and expr.endswith('"')) or \
           (expr.startswith("'") and expr.endswith("'")):
            return expr[1:-1]

        # Literal number
        try:
            if '.' in expr:
                return float(expr)
            else:
                return int(expr)
        except ValueError:
            pass

        # Literal boolean
        if expr.lower() == 'true':
            return True
        elif expr.lower() == 'false':
            return False
        elif expr.lower() == 'null' or expr.lower() == 'none':
            return None

        # Return as-is
        return expr

    def _evaluate_assertion(self, expr: str) -> bool:
        """Evaluate an assertion expression."""
        # Simple comparison operators
        operators = ['==', '!=', '>=', '<=', '>', '<', 'in', 'not in']

        for op in operators:
            if op in expr:
                parts = expr.split(op, 1)
                if len(parts) == 2:
                    left = self._evaluate_expression(parts[0].strip())
                    right = self._evaluate_expression(parts[1].strip())

                    if op == '==':
                        return left == right
                    elif op == '!=':
                        return left != right
                    elif op == '>':
                        return left > right
                    elif op == '<':
                        return left < right
                    elif op == '>=':
                        return left >= right
                    elif op == '<=':
                        return left <= right
                    elif op == 'in':
                        return left in right
                    elif op == 'not in':
                        return left not in right

        # Boolean expression
        result = self._evaluate_expression(expr)
        return bool(result)
