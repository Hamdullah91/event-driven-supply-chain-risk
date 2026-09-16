"""
Core event taxonomy and severity levels used across the supply-chain system.

The six classifier categories are the canonical event taxonomy.  Historical
aliases remain accepted at ingestion boundaries, but persisted events use the
canonical lowercase values defined here.
"""

from enum import StrEnum


class EventType(StrEnum):
    """Canonical supply-chain event categories produced by the classifier."""

    SUPPLY_DISRUPTION = "supply_disruption"
    REGULATION_CHANGE = "regulation_change"
    FACILITY_OUTAGE = "facility_outage"
    TECHNOLOGY_EMBARGO = "technology_embargo"
    TRADE_POLICY_CHANGE = "trade_policy_change"
    QUOTA_CHANGE = "quota_change"


class EventSeverity(StrEnum):
    """Standard severity levels for supply chain events."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"
    UNKNOWN = "unknown"
