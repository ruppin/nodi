"""Request history management for Nodi."""

import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict


@dataclass
class HistoryEntry:
    """Single history entry."""

    timestamp: str
    method: str
    service: str
    environment: str
    url: str
    status_code: int
    elapsed_ms: float
    request_data: Optional[Dict] = None

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict) -> "HistoryEntry":
        """Create from dictionary."""
        return cls(**data)


class HistoryManager:
    """Manage request history."""

    def __init__(self, history_file: Optional[Path] = None, max_entries: int = 1000):
        if history_file is None:
            history_file = Path.home() / ".nodi" / "history.json"

        self.history_file = history_file
        self.max_entries = max_entries
        self.entries: List[HistoryEntry] = []

        # Create directory if needed
        self.history_file.parent.mkdir(parents=True, exist_ok=True)

        # Load existing history
        self.load()

    def add(
        self,
        method: str,
        service: str,
        environment: str,
        url: str,
        status_code: int,
        elapsed_ms: float,
        request_data: Optional[Dict] = None,
    ):
        """Add entry to history."""
        entry = HistoryEntry(
            timestamp=datetime.now().isoformat(),
            method=method,
            service=service,
            environment=environment,
            url=url,
            status_code=status_code,
            elapsed_ms=elapsed_ms,
            request_data=request_data,
        )

        self.entries.append(entry)

        # Trim if needed
        if len(self.entries) > self.max_entries:
            self.entries = self.entries[-self.max_entries :]

        # Save
        self.save()

    def get_recent(self, count: int = 10) -> List[HistoryEntry]:
        """Get recent entries."""
        return self.entries[-count:]

    def search(self, query: str) -> List[HistoryEntry]:
        """Search history entries."""
        query = query.lower()
        results = []

        for entry in self.entries:
            if (
                query in entry.service.lower()
                or query in entry.environment.lower()
                or query in entry.url.lower()
                or query in entry.method.lower()
            ):
                results.append(entry)

        return results

    def get_by_index(self, index: int) -> Optional[HistoryEntry]:
        """Get entry by index (1-based, most recent = 1)."""
        try:
            # Convert to 0-based index from end
            return self.entries[-(index)]
        except IndexError:
            return None

    def clear(self):
        """Clear all history."""
        self.entries.clear()
        self.save()

    def save(self):
        """Save history to file."""
        try:
            data = [entry.to_dict() for entry in self.entries]
            with open(self.history_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Warning: Failed to save history: {e}")

    def load(self):
        """Load history from file."""
        if not self.history_file.exists():
            return

        try:
            with open(self.history_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.entries = [HistoryEntry.from_dict(entry) for entry in data]
        except Exception as e:
            print(f"Warning: Failed to load history: {e}")

    def export(self, output_file: Path):
        """Export history to file."""
        data = [entry.to_dict() for entry in self.entries]
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def format_entries(self, entries: List[HistoryEntry]) -> str:
        """Format entries for display."""
        if not entries:
            return "No history entries found"

        lines = []
        for i, entry in enumerate(reversed(entries), 1):
            status_icon = "✓" if 200 <= entry.status_code < 300 else "✗"
            lines.append(
                f"{i:3d}. {status_icon} {entry.method:6s} {entry.service}.{entry.environment} "
                f"{entry.url} ({entry.status_code}, {entry.elapsed_ms:.0f}ms)"
            )

        return "\n".join(lines)
