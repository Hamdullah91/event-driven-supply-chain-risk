from __future__ import annotations

from enum import StrEnum
from typing import Any, Mapping


class EvidenceAvailability(StrEnum):
    AVAILABLE = "AVAILABLE"
    PARTIAL = "PARTIAL"
    UNAVAILABLE = "UNAVAILABLE"


def event_evidence_availability(properties: Mapping[str, Any]) -> EvidenceAvailability:
    """Classify Event provenance without inventing missing metadata."""

    core_values = (
        properties.get("source"),
        properties.get("timestamp"),
        properties.get("confidence"),
    )
    populated = sum(value not in (None, "") for value in core_values)
    if populated == len(core_values):
        return EvidenceAvailability.AVAILABLE
    if populated > 0 or properties.get("source_url") or properties.get("description"):
        return EvidenceAvailability.PARTIAL
    return EvidenceAvailability.UNAVAILABLE


def relationship_evidence_availability(
    properties: Mapping[str, Any],
) -> EvidenceAvailability:
    """Classify heterogeneous relationship provenance conservatively.

    Seeded, extracted, derived, and dynamic links intentionally use different
    provenance fields, so availability is based on truthful evidence presence
    rather than one fabricated universal schema.
    """

    has_source = any(
        properties.get(key) not in (None, "")
        for key in ("source_type", "source", "source_url")
    )
    has_support = any(
        properties.get(key) not in (None, "")
        for key in (
            "confidence",
            "verification_status",
            "derivation",
            "link_method",
            "linked_at",
        )
    )

    if has_source and has_support:
        return EvidenceAvailability.AVAILABLE
    if has_source or has_support:
        return EvidenceAvailability.PARTIAL
    return EvidenceAvailability.UNAVAILABLE
