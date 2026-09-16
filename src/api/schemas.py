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


class EventSeverity(str, Enum):
    UNKNOWN = "unknown"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class EventRequest(BaseModel):
    event_type: EventType = Field(..., description="The classified supply-chain event type.")
    entity: str = Field(min_length=1, max_length=200, description="The entity associated with the event.")
    severity: EventSeverity = Field(..., description="Canonical categorical event severity used by the risk engine.")


class EventDetail(BaseModel):
    event_id: str
    event_type: str
    source: str
    timestamp: Any
    entity_id: str | None = None
    severity: EventSeverity
    payload: dict[str, Any] = Field(default_factory=dict)
    created_at: Any | None = None


class EventListResponse(BaseModel):
    events: list[EventDetail] = Field(default_factory=list)
    count: int = Field(ge=0)
    limit: int = Field(ge=1, le=500)
    offset: int = Field(ge=0)


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


class RiskSummary(BaseModel):
    company_id: str
    risk_score: float = Field(ge=0.0, le=1.0)
    risk_level: str
    contributing_event_count: int = Field(ge=0)
    max_hops: int = Field(ge=1, le=3)


class BlastRadiusCompany(BaseModel):
    company_id: str
    company_name: str
    hop_distance: int = Field(ge=1, le=3)
    transmission_factor: float = Field(ge=0.0, le=1.0)
    path: list[dict[str, Any]] = Field(default_factory=list)


class BlastRadiusResponse(BaseModel):
    company_id: str
    max_hops: int = Field(ge=1, le=3)
    affected_company_count: int = Field(ge=0)
    hop_counts: dict[str, int] = Field(default_factory=dict)
    companies: list[BlastRadiusCompany] = Field(default_factory=list)


class EventBlastRadiusCompany(BaseModel):
    company_id: str
    company_name: str
    origin_company_id: str
    origin_company_name: str
    hop_distance: int = Field(ge=0, le=3)
    initial_risk: float = Field(ge=0.0, le=1.0)
    path_dependency: float = Field(ge=0.0, le=1.0)
    distance_decay: float = Field(ge=0.0, le=1.0)
    propagated_risk: float = Field(ge=0.0, le=1.0)
    path: list[dict[str, Any]] = Field(default_factory=list)


class EventBlastRadiusResponse(BaseModel):
    event_id: str
    event_type: str | None = None
    severity: EventSeverity | None = None
    max_hops: int = Field(ge=1, le=3)
    affected_company_count: int = Field(ge=0)
    hop_counts: dict[str, int] = Field(default_factory=dict)
    companies: list[EventBlastRadiusCompany] = Field(default_factory=list)


class EventExposure(BaseModel):
    event_id: str
    event_type: str | None = None
    severity: EventSeverity
    timestamp: Any | None = None
    source: str | None = None
    confidence: float | None = None
    description: str | None = None
    affected_company_id: str
    affected_company_name: str
    hop_distance: int = Field(ge=0, le=3)
    initial_risk: float = Field(ge=0.0, le=1.0)
    path_dependency: float = Field(ge=0.0, le=1.0)
    distance_decay: float = Field(ge=0.0, le=1.0)
    propagated_risk: float = Field(ge=0.0, le=1.0)
    path: list[dict[str, Any]] = Field(default_factory=list)


class CompanyExposureResponse(BaseModel):
    company_id: str
    event_count: int = Field(ge=0)
    exposures: list[EventExposure] = Field(default_factory=list)
