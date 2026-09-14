from enum import Enum

from pydantic import BaseModel, Field


class EventType(str, Enum):
    SUPPLY_DISRUPTION = "SUPPLY_DISRUPTION"
    REGULATION_CHANGE = "REGULATION_CHANGE"
    FACILITY_OUTAGE = "FACILITY_OUTAGE"
    TECHNOLOGY_EMBARGO = "TECHNOLOGY_EMBARGO"
    TRADE_POLICY_CHANGE = "TRADE_POLICY_CHANGE"
    QUOTA_CHANGE = "QUOTA_CHANGE"


class EventRequest(BaseModel):
    event_type: EventType = Field(
        ...,
        description="The classified supply-chain event type.",
    )
    entity: str = Field(
        min_length=1,
        max_length=200,
        description="The entity associated with the event.",
    )
    severity: float = Field(
        ge=0.0,
        le=1.0,
        description="Normalized event severity between 0 and 1.",
    )
