"""
Standard event types and severity levels used by the
supply chain intelligence system.
"""

from enum import StrEnum


class EventType(StrEnum):
    """
    Supported supply chain event categories.
    """

    FACILITY_SHUTDOWN = "facility_shutdown"
    SUPPLY_DISRUPTION = "supply_disruption"
    CAPACITY_CHANGE = "capacity_change"

    EARNINGS_WARNING = "earnings_warning"
    DEMAND_CHANGE = "demand_change"

    GEOPOLITICAL_EVENT = "geopolitical_event"
    NATURAL_DISASTER = "natural_disaster"
    REGULATORY_CHANGE = "regulatory_change"

    COMPANY_ACQUISITION = "company_acquisition"
    COMPANY_PARTNERSHIP = "company_partnership"

    PRODUCT_LAUNCH = "product_launch"
    PRODUCTION_CHANGE = "production_change"

    OTHER = "other"


class EventSeverity(StrEnum):
    """
    Standard severity levels for supply chain events.
    """

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"
    UNKNOWN = "unknown"