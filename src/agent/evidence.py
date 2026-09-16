from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

from src.events.types import EventSeverity


class EvidenceStatus(str, Enum):
    SUFFICIENT = "SUFFICIENT"
    PARTIAL = "PARTIAL"
    INSUFFICIENT = "INSUFFICIENT"


class GraphNodeEvidence(BaseModel):
    ref: str = Field(min_length=1)
    labels: list[str] = Field(default_factory=list)
    properties: dict[str, Any] = Field(default_factory=dict)


class GraphRelationshipEvidence(BaseModel):
    ref: str = Field(min_length=1)
    relationship_type: str = Field(min_length=1)
    start_node_ref: str | None = None
    end_node_ref: str | None = None
    properties: dict[str, Any] = Field(default_factory=dict)


class GraphPathEvidence(BaseModel):
    path_id: str = Field(min_length=1)
    nodes: list[GraphNodeEvidence]
    relationships: list[GraphRelationshipEvidence]
    hop_count: int = Field(ge=0, le=3)


class EventEvidence(BaseModel):
    ref: str = Field(min_length=1)
    event_id: str | None = None
    event_type: str | None = None
    timestamp: str | None = None
    severity: EventSeverity | None = None
    confidence: float | None = None
    description: str | None = None
    source: str | None = None
    linked_entity_ref: str | None = None
    linked_entity_id: str | None = None
    linked_entity_name: str | None = None
    linkage_type: str | None = None


class EvidenceBundle(BaseModel):
    question: str = Field(min_length=1)
    cypher: str = Field(min_length=1)
    query_results: list[dict[str, Any]] = Field(default_factory=list)
    paths: list[GraphPathEvidence] = Field(default_factory=list)
    events: list[EventEvidence] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class PathFinding(BaseModel):
    path_id: str
    hop_count: int = Field(ge=0, le=3)
    entities: list[str] = Field(default_factory=list)
    relationship_types: list[str] = Field(default_factory=list)
    linked_events: list[str] = Field(default_factory=list)


class EvidenceAssessment(BaseModel):
    status: EvidenceStatus
    relevant_paths: list[PathFinding] = Field(default_factory=list)
    relevant_events: list[str] = Field(default_factory=list)
    evidence_notes: list[str] = Field(default_factory=list)
    missing_evidence: list[str] = Field(default_factory=list)


def _display_name(node: GraphNodeEvidence) -> str:
    for key in ("name", "company_name", "facility_name", "material_name", "product_name", "company_id", "facility_id", "id"):
        value = node.properties.get(key)
        if value not in (None, ""):
            return str(value)
    return node.ref


def assess_evidence(bundle: EvidenceBundle) -> EvidenceAssessment:
    event_by_entity: dict[str, list[str]] = {}
    for event in bundle.events:
        if event.linked_entity_ref:
            event_by_entity.setdefault(event.linked_entity_ref, []).append(event.ref)

    findings: list[PathFinding] = []
    relevant_event_refs: set[str] = set()

    for path in bundle.paths:
        path_event_refs: set[str] = set()
        for node in path.nodes:
            path_event_refs.update(event_by_entity.get(node.ref, []))
        relevant_event_refs.update(path_event_refs)
        findings.append(PathFinding(
            path_id=path.path_id,
            hop_count=path.hop_count,
            entities=[_display_name(node) for node in path.nodes],
            relationship_types=[rel.relationship_type for rel in path.relationships],
            linked_events=sorted(path_event_refs),
        ))

    notes = list(bundle.warnings)
    missing: list[str] = []
    if not findings:
        missing.append("No valid 1-to-3-hop graph path was retrieved.")
    if not bundle.events:
        missing.append("No Event node was connected to the retrieved path entities.")

    if findings and relevant_event_refs:
        status = EvidenceStatus.SUFFICIENT
        notes.insert(0, "Graph paths and linked event evidence were retrieved.")
    elif findings or bundle.events:
        status = EvidenceStatus.PARTIAL
        notes.insert(0, "Some graph evidence was retrieved, but event/path evidence is incomplete.")
    else:
        status = EvidenceStatus.INSUFFICIENT
        notes.insert(0, "The retrieved data is insufficient for a graph-grounded risk conclusion.")

    return EvidenceAssessment(
        status=status,
        relevant_paths=findings,
        relevant_events=sorted(relevant_event_refs),
        evidence_notes=notes,
        missing_evidence=missing,
    )
