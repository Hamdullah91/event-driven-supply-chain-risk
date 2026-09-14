from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class EventType(str, Enum):
    SUPPLY_DISRUPTION = "SUPPLY_DISRUPTION"
    REGULATION_CHANGE = "REGULATION_CHANGE"
    FACILITY_OUTAGE = "FACILITY_OUTAGE"
    TECHNOLOGY_EMBARGO = "TECHNOLOGY_EMBARGO"
    TRADE_POLICY_CHANGE = "TRADE_POLICY_CHANGE"
    QUOTA_CHANGE = "QUOTA_CHANGE"


class EventRequest(BaseModel):
    event_type: EventType = Field(..., description="The classified supply-chain event type.")
    entity: str = Field(min_length=1, max_length=200, description="The entity associated with the event.")
    severity: float = Field(ge=0.0, le=1.0, description="Normalized event severity between 0 and 1.")


class CompanySummary(BaseModel):
    company_id: str
    name: str
    legal_name: str | None = None
    entity_type: str | None = None
    industry_id: str | None = None


class CompanyListResponse(BaseModel):
    companies: list[CompanySummary]
    count: int = Field(ge=0)
    limit: int = Field(ge=1, le=500)
    offset: int = Field(ge=0)


class CompanyDetail(CompanySummary):
    seed_source: str | None = None
    facilities: list[str] = Field(default_factory=list)
    products: list[str] = Field(default_factory=list)
    materials: list[str] = Field(default_factory=list)
    technologies: list[str] = Field(default_factory=list)


class GraphNode(BaseModel):
    id: str
    label: str
    name: str
    properties: dict[str, Any] = Field(default_factory=dict)


class GraphRelationship(BaseModel):
    id: str
    source: str
    target: str
    relationship_type: str
    properties: dict[str, Any] = Field(default_factory=dict)


class CompanyNetwork(BaseModel):
    company_id: str
    depth: int = Field(ge=1, le=3)
    nodes: list[GraphNode] = Field(default_factory=list)
    relationships: list[GraphRelationship] = Field(default_factory=list)
