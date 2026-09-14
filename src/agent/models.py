from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class Intent(str, Enum):
    GRAPH_LOOKUP = "GRAPH_LOOKUP"
    RISK_ANALYSIS = "RISK_ANALYSIS"
    EVENT_LOOKUP = "EVENT_LOOKUP"
    DOCUMENT_LOOKUP = "DOCUMENT_LOOKUP"
    GENERAL = "GENERAL"


class ToolName(str, Enum):
    GRAPH_QUERY = "GRAPH_QUERY"
    COMPANY_NETWORK = "COMPANY_NETWORK"
    RISK_ENGINE = "RISK_ENGINE"
    EVENT_SEARCH = "EVENT_SEARCH"
    DOCUMENT_SEARCH = "DOCUMENT_SEARCH"
    NONE = "NONE"


class EntityReference(BaseModel):
    name: str = Field(min_length=1)
    entity_type: str | None = None


class AgentPlan(BaseModel):
    intent: Intent
    tool: ToolName
    objective: str = Field(min_length=1)
    entities: list[EntityReference] = Field(default_factory=list)
    requires_generated_cypher: bool = False
    max_hops: int = Field(default=3, ge=0, le=3)


class CypherProposal(BaseModel):
    cypher: str = Field(min_length=1)
    parameters: dict[str, Any] = Field(default_factory=dict)
    expected_fields: list[str] = Field(default_factory=list)
