"""
Alert records and in-memory store with configurable retention.

Provides a ring-buffer alert store for budget-related events,
serializable for persistence.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class AlertLevel(Enum):
    """Severity levels for budget alerts."""

    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"

    def __lt__(self, other: AlertLevel) -> bool:
        order = [AlertLevel.INFO, AlertLevel.WARNING, AlertLevel.CRITICAL]
        return order.index(self) < order.index(other)

    def __le__(self, other: AlertLevel) -> bool:
        return self == other or self < other

    def __gt__(self, other: AlertLevel) -> bool:
        return not self <= other

    def __ge__(self, other: AlertLevel) -> bool:
        return not self < other


class AlertRecord:
    """A single alert record with timestamp, workflow, severity, and message."""

    def __init__(self, workflow: str, level: AlertLevel, message: str) -> None:
        self.timestamp: str = datetime.now(timezone.utc).isoformat()
        self.workflow: str = workflow
        self.level: AlertLevel = level
        self.message: str = message

    def to_dict(self) -> dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "workflow": self.workflow,
            "level": self.level.value,
            "message": self.message,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> AlertRecord:
        record = cls.__new__(cls)
        record.timestamp = data.get("timestamp", "")
        record.workflow = data.get("workflow", "")
        record.level = AlertLevel(data.get("level", "info"))
        record.message = data.get("message", "")
        return record


class AlertStore:
    """Configurable in-memory alert store with a retention limit (ring buffer)."""

    def __init__(self, max_records: int = 100) -> None:
        self._max_records: int = max_records
        self._records: list[AlertRecord] = []

    def push(self, alert: AlertRecord) -> None:
        """Push a new alert. Evicts oldest if at capacity."""
        if len(self._records) >= self._max_records:
            self._records.pop(0)
        self._records.append(alert)

    def all(self) -> list[AlertRecord]:
        """Return all stored alerts, oldest first."""
        return list(self._records)

    def filter_by_level(self, min_level: AlertLevel) -> list[AlertRecord]:
        """Return alerts of at least the given severity."""
        return [a for a in self._records if a.level >= min_level]

    def __len__(self) -> int:
        return len(self._records)

    def is_empty(self) -> bool:
        return len(self._records) == 0

    def clear(self) -> None:
        self._records.clear()

    def to_json(self) -> str:
        """Serialize to JSON string."""
        return json.dumps({
            "max_records": self._max_records,
            "records": [r.to_dict() for r in self._records],
        })

    @classmethod
    def from_json(cls, data: str) -> AlertStore:
        """Deserialize from JSON string."""
        parsed = json.loads(data)
        store = cls(parsed.get("max_records", 100))
        for r_data in parsed.get("records", []):
            store.push(AlertRecord.from_dict(r_data))
        return store
