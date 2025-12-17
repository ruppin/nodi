"""JSON filtering support using jq."""

from typing import Any, Optional
import json


class JSONFilter:
    """JSON filtering using jq-like syntax."""

    def __init__(self):
        self.pyjq_available = False
        try:
            import pyjq

            self.pyjq = pyjq
            self.pyjq_available = True
        except ImportError:
            # Fallback to jsonpath if pyjq not available
            try:
                from jsonpath_ng import jsonpath
                from jsonpath_ng.ext import parse

                self.jsonpath_parse = parse
                self.pyjq_available = False
            except ImportError:
                pass

    def apply(self, data: Any, filter_expression: str) -> Any:
        """
        Apply filter expression to data.

        Args:
            data: Data to filter (usually dict or list)
            filter_expression: jq-style filter expression

        Returns:
            Filtered data
        """
        if not filter_expression or filter_expression == ".":
            return data

        # Try pyjq first
        if self.pyjq_available:
            try:
                return self._apply_pyjq(data, filter_expression)
            except Exception as e:
                # Fall back to simple filters
                return self._apply_simple_filter(data, filter_expression)
        else:
            # Use simple filter
            return self._apply_simple_filter(data, filter_expression)

    def _apply_pyjq(self, data: Any, filter_expression: str) -> Any:
        """Apply filter using pyjq library."""
        result = self.pyjq.all(filter_expression, data)

        # If single result, unwrap it
        if len(result) == 1:
            return result[0]

        return result

    def _apply_simple_filter(self, data: Any, filter_expression: str) -> Any:
        """Apply simple filter expressions without pyjq."""
        # Handle common simple cases
        expr = filter_expression.strip()

        # . -> identity
        if expr == ".":
            return data

        # .field -> get field
        if expr.startswith(".") and not "[" in expr and not "|" in expr:
            field = expr[1:]
            if isinstance(data, dict):
                return data.get(field)

        # .[n] or .[start:end] or .[start:end:step] -> array index or slice
        if expr.startswith(".[") and expr.endswith("]") and "." not in expr[2:-1]:
            try:
                slice_str = expr[2:-1]

                # Check if it's a slice (contains ':')
                if ':' in slice_str:
                    # Parse slice notation: [start:end] or [start:end:step]
                    parts = slice_str.split(':')
                    start = int(parts[0]) if parts[0] else None
                    end = int(parts[1]) if len(parts) > 1 and parts[1] else None
                    step = int(parts[2]) if len(parts) > 2 and parts[2] else None

                    if isinstance(data, list):
                        return data[start:end:step] if step else data[start:end]
                else:
                    # Simple integer index
                    index = int(slice_str)
                    if isinstance(data, list):
                        return data[index]
            except (ValueError, IndexError):
                pass

        # .[] -> iterate array
        if expr == ".[]":
            if isinstance(data, list):
                return data
            elif isinstance(data, dict):
                return list(data.values())

        # .[].field -> map field from array (equivalent to .[*].field)
        if expr.startswith(".[]") and len(expr) > 3 and expr[3] == ".":
            if isinstance(data, list):
                field_path = expr[4:]  # Remove .[]
                parts = field_path.split(".")
                results = []
                for item in data:
                    result = item
                    for part in parts:
                        if isinstance(result, dict):
                            result = result.get(part)
                        else:
                            result = None
                            break
                    if result is not None:
                        results.append(result)
                return results

        # length
        if expr == "length":
            if isinstance(data, (list, dict, str)):
                return len(data)

        # keys
        if expr == "keys":
            if isinstance(data, dict):
                return sorted(list(data.keys()))

        # values
        if expr == "values":
            if isinstance(data, dict):
                return list(data.values())

        # type
        if expr == "type":
            if isinstance(data, dict):
                return "object"
            elif isinstance(data, list):
                return "array"
            elif isinstance(data, str):
                return "string"
            elif isinstance(data, int):
                return "number"
            elif isinstance(data, bool):
                return "boolean"
            elif data is None:
                return "null"

        # Nested field access like .a.b.c
        if expr.startswith(".") and "." in expr[1:] and "[" not in expr:
            parts = expr[1:].split(".")
            result = data
            for part in parts:
                if isinstance(result, dict):
                    result = result.get(part)
                else:
                    return None
            return result

        # Array expansion with field like .[*].field or .[].field
        if expr.startswith(".[") and ("*" in expr or expr.startswith(".[].")):
            try:
                # Parse .[*].field or .[].field
                if ".[*]" in expr:
                    remaining = expr[expr.index(".[*]") + 4:]
                elif ".[]" in expr:
                    remaining = expr[expr.index(".[]") + 3:]
                else:
                    remaining = ""

                if isinstance(data, list) and remaining.startswith("."):
                    # Extract field path
                    parts = remaining[1:].split(".")
                    results = []
                    for item in data:
                        result = item
                        for part in parts:
                            if isinstance(result, dict):
                                result = result.get(part)
                            else:
                                result = None
                                break
                        if result is not None:
                            results.append(result)
                    return results
            except (ValueError, IndexError):
                pass

        # Array index with field like .[0].name
        if expr.startswith(".[") and "." in expr and "*" not in expr:
            try:
                # Parse .[n].field or .[n].field.nested
                bracket_end = expr.index("]")
                index_str = expr[2:bracket_end]

                # Skip if it's .[*] or .[] (handled above)
                if index_str == "*" or index_str == "":
                    pass
                else:
                    index = int(index_str)
                    remaining = expr[bracket_end + 1:]

                    if isinstance(data, list) and 0 <= index < len(data):
                        result = data[index]
                        # Now apply the rest of the path
                        if remaining.startswith("."):
                            parts = remaining[1:].split(".")
                            for part in parts:
                                if isinstance(result, dict):
                                    result = result.get(part)
                                else:
                                    return None
                        return result
            except (ValueError, IndexError):
                pass

        # If we can't handle it, return error message
        return f"Filter '{filter_expression}' not supported in simple mode. Install pyjq for full jq support."


def format_filtered_output(data: Any, colored: bool = True) -> str:
    """Format filtered output."""
    if isinstance(data, (dict, list)):
        if colored:
            try:
                from pygments import highlight
                from pygments.lexers import JsonLexer
                from pygments.formatters import TerminalFormatter

                json_str = json.dumps(data, indent=2, ensure_ascii=False)
                return highlight(json_str, JsonLexer(), TerminalFormatter())
            except Exception:
                return json.dumps(data, indent=2, ensure_ascii=False)
        else:
            return json.dumps(data, indent=2, ensure_ascii=False)
    else:
        return str(data)
