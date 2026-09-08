from __future__ import annotations

from datetime import datetime
from uuid import NAMESPACE_URL, UUID, uuid5

from src.events.models import SupplyChainEvent
from src.events.types import EventSeverity, EventType


CLASSIFIER_EVENT_TYPE_MAP: dict[str, EventType] = {
    "FACILITY_OUTAGE": EventType.FACILITY_SHUTDOWN,
    "FACILITY_SHUTDOWN": EventType.FACILITY_SHUTDOWN,
    "SUPPLY_DISRUPTION": EventType.SUPPLY_DISRUPTION,
    "REGULATION_CHANGE": EventType.REGULATORY_CHANGE,
    "REGULATORY_CHANGE": EventType.REGULATORY_CHANGE,
    "GEOPOLITICAL_EVENT": EventType.GEOPOLITICAL_EVENT,
}


def normalize_classifier_event_type(label: str) -> EventType:
    normalized = label.strip().upper()

    try:
        return CLASSIFIER_EVENT_TYPE_MAP[normalized]
    except KeyError as exc:
        raise ValueError(
            f"Unsupported classifier event label: {label}"
        ) from exc


def generate_event_id(
    *,
    article_id: str,
    event_type: EventType,
    entity_id: str | None = None,
) -> UUID:
    normalized_entity = (
        entity_id.strip().upper()
        if entity_id
        else "UNKNOWN"
    )

    canonical = "|".join(
        [
            article_id.strip(),
            event_type.value,
            normalized_entity,
        ]
    )

    return uuid5(
        NAMESPACE_URL,
        canonical,
    )


def build_news_event(
    *,
    article_id: str,
    classifier_label: str,
    source: str,
    timestamp: datetime,
    confidence: float,
    title: str,
    entity_id: str | None = None,
    severity: EventSeverity = EventSeverity.UNKNOWN,
    source_url: str | None = None,
) -> SupplyChainEvent:
    if not article_id.strip():
        raise ValueError("article_id cannot be empty.")

    if not title.strip():
        raise ValueError("title cannot be empty.")

    if not 0.0 <= confidence <= 1.0:
        raise ValueError(
            "confidence must be between 0.0 and 1.0."
        )

    event_type = normalize_classifier_event_type(
        classifier_label
    )

    event_id = generate_event_id(
        article_id=article_id,
        event_type=event_type,
        entity_id=entity_id,
    )

    return SupplyChainEvent(
        event_id=event_id,
        event_type=event_type,
        source=source,
        timestamp=timestamp,
        entity_id=entity_id,
        severity=severity,
        payload={
            "article_id": article_id,
            "title": title,
            "confidence": confidence,
            "source_url": source_url,
        },
    )