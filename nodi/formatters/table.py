"""Table formatter for Nodi."""

from typing import Any, List, Dict
from rich.console import Console
from rich.table import Table
from tabulate import tabulate


class TableFormatter:
    """Format responses as ASCII tables."""

    def __init__(self, use_rich: bool = True):
        self.use_rich = use_rich
        self.console = Console() if use_rich else None

    def format(self, data: Any) -> str:
        """Format data as table."""
        if data is None:
            return ""

        # Convert data to table format
        if isinstance(data, list):
            if not data:
                return "Empty list"

            # List of dictionaries -> table
            if isinstance(data[0], dict):
                return self._format_dict_list(data)
            # List of primitives -> single column table
            else:
                return self._format_list(data)

        elif isinstance(data, dict):
            # Single dict -> vertical table (key-value pairs)
            return self._format_dict(data)

        else:
            # Primitive value
            return str(data)

    def _format_dict_list(self, data: List[Dict]) -> str:
        """Format list of dictionaries as table."""
        if not data:
            return ""

        if self.use_rich:
            return self._format_dict_list_rich(data)
        else:
            return self._format_dict_list_tabulate(data)

    def _format_dict_list_rich(self, data: List[Dict]) -> str:
        """Format using rich library."""
        # Get all unique keys
        keys = set()
        for item in data:
            keys.update(item.keys())
        keys = sorted(list(keys))

        # Create table
        table = Table(show_header=True, header_style="bold cyan")

        # Add columns
        for key in keys:
            table.add_column(str(key))

        # Add rows
        for item in data:
            row = [str(item.get(key, "")) for key in keys]
            table.add_row(*row)

        # Render to string
        console = Console(record=True)
        console.print(table)
        return console.export_text()

    def _format_dict_list_tabulate(self, data: List[Dict]) -> str:
        """Format using tabulate library."""
        return tabulate(data, headers="keys", tablefmt="grid")

    def _format_list(self, data: List) -> str:
        """Format simple list as table."""
        table_data = [[i, str(item)] for i, item in enumerate(data)]
        return tabulate(table_data, headers=["Index", "Value"], tablefmt="grid")

    def _format_dict(self, data: Dict) -> str:
        """Format dictionary as vertical table."""
        table_data = [[key, str(value)] for key, value in data.items()]
        return tabulate(table_data, headers=["Key", "Value"], tablefmt="grid")
