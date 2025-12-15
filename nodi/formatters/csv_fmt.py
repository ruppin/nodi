"""CSV formatter for Nodi."""

import csv
import io
from typing import Any, List, Dict


class CSVFormatter:
    """Format responses as CSV."""

    def __init__(self):
        pass

    def format(self, data: Any) -> str:
        """Format data as CSV."""
        if data is None:
            return ""

        if isinstance(data, list):
            if not data:
                return ""

            # List of dictionaries
            if isinstance(data[0], dict):
                return self._format_dict_list(data)
            # List of primitives
            else:
                return self._format_list(data)

        elif isinstance(data, dict):
            # Single dict -> two columns (key, value)
            return self._format_dict(data)

        else:
            # Primitive value
            return str(data)

    def _format_dict_list(self, data: List[Dict]) -> str:
        """Format list of dictionaries as CSV."""
        if not data:
            return ""

        # Get all unique keys
        keys = set()
        for item in data:
            keys.update(item.keys())
        keys = sorted(list(keys))

        # Write CSV
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=keys)
        writer.writeheader()
        writer.writerows(data)

        return output.getvalue()

    def _format_list(self, data: List) -> str:
        """Format simple list as CSV."""
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["Value"])
        for item in data:
            writer.writerow([item])

        return output.getvalue()

    def _format_dict(self, data: Dict) -> str:
        """Format dictionary as CSV."""
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["Key", "Value"])
        for key, value in data.items():
            writer.writerow([key, value])

        return output.getvalue()
