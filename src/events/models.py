"""
Core event models for the event-driven supply chain system.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import UUID, uuid4

from src.events.types import EventSeverity, EventType


@dataclass(slots=True)
class SupplyChainEvent:
    """
    Represents a normalized event entering the supply chain
    intelligence pipeline.
    """

    event_type: EventType
    source: str
    timestamp: datetime

    entity_id: str | None = None
    severity: EventSeverity = EventSeverity.UNKNOWN

    payload: dict[str, Any] = field(default_factory=dict)

    event_id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    def __post_init__(self) -> None:
        """
        Validate the core event fields.
        """

        if not self.source.strip():
            raise ValueError("Event source cannot be empty.")

        if self.entity_id is not None and not self.entity_id.strip():
            raise ValueError(
                "Entity ID cannot be an empty string."
            )

        if self.timestamp.tzinfo is None:
            raise ValueError(
                "Event timestamp must be timezone-aware."
            )