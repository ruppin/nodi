"""YAML formatter for Nodi."""

import yaml
from typing import Any


class YAMLFormatter:
    """Format responses as YAML."""

    def __init__(self):
        pass

    def format(self, data: Any) -> str:
        """Format data as YAML."""
        if data is None:
            return ""

        try:
            return yaml.dump(
                data,
                default_flow_style=False,
                allow_unicode=True,
                sort_keys=False,
            )
        except Exception as e:
            return f"Error formatting YAML: {str(e)}"

    def format_with_metadata(self, data: Any, metadata: dict) -> str:
        """Format YAML with metadata header."""
        output = []

        # Add metadata as comment
        if metadata:
            output.append("# Metadata")
            for key, value in metadata.items():
                output.append(f"# {key}: {value}")
            output.append("")

        # Add data
        output.append(self.format(data))

        return "\n".join(output)
