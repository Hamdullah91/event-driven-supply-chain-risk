"""
Factory for creating normalized supply chain events.
"""

from datetime import datetime, timezone
from typing import Any

from src.events.models import SupplyChainEvent
from src.events.types import EventSeverity, EventType


def create_event(
    *,
    event_type: EventType,
    source: str,
    entity_id: str | None = None,
    severity: EventSeverity = EventSeverity.UNKNOWN,
    payload: dict[str, Any] | None = None,
    timestamp: datetime | None = None,
) -> SupplyChainEvent:
    """
    Create a validated SupplyChainEvent with sensible defaults.
    """

    if payload is None:
        payload = {}

    if timestamp is None:
        timestamp = datetime.now(timezone.utc)

    return SupplyChainEvent(
        event_type=event_type,
        source=source,
        timestamp=timestamp,
        entity_id=entity_id,
        severity=severity,
        payload=payload,
    )