"""JSON formatter for Nodi."""

import json
from typing import Any
from pygments import highlight
from pygments.lexers import JsonLexer
from pygments.formatters import TerminalFormatter


class JSONFormatter:
    """Format JSON responses."""

    def __init__(self, colored: bool = True, compact: bool = False):
        self.colored = colored
        self.compact = compact

    def format(self, data: Any) -> str:
        """Format data as JSON."""
        if data is None:
            return ""

        # Convert to JSON string
        if self.compact:
            json_str = json.dumps(data, ensure_ascii=False)
        else:
            json_str = json.dumps(data, indent=2, ensure_ascii=False)

        # Add syntax highlighting if enabled
        if self.colored:
            try:
                json_str = highlight(json_str, JsonLexer(), TerminalFormatter())
            except Exception:
                # Fall back to plain JSON if highlighting fails
                pass

        return json_str

    def format_with_metadata(self, data: Any, metadata: dict) -> str:
        """Format JSON with metadata header."""
        output = []

        # Add metadata
        if metadata:
            output.append(self._format_metadata(metadata))
            output.append("")

        # Add data
        output.append(self.format(data))

        return "\n".join(output)

    def _format_metadata(self, metadata: dict) -> str:
        """Format metadata as header."""
        lines = []

        if "method" in metadata and "url" in metadata:
            lines.append(f"{metadata['method']} {metadata['url']}")

        if "status_code" in metadata:
            status = metadata["status_code"]
            reason = metadata.get("reason_phrase", "")
            elapsed = metadata.get("elapsed_time")

            status_line = f"Status: {status}"
            if reason:
                status_line += f" {reason}"
            if elapsed:
                status_line += f" ({elapsed:.0f}ms)"

            lines.append(status_line)

        return "\n".join(lines)
