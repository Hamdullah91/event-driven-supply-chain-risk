from __future__ import annotations

from dataclasses import dataclass

from src.graph.provenance.models import ProvenanceMetadata


@dataclass(frozen=True, slots=True)
class GraphIngestionRelationship:
    subject: str
    subject_type: str

    relationship: str

    object: str
    object_type: str

    provenance: ProvenanceMetadata


@dataclass(frozen=True, slots=True)
class GraphIngestionResult:
    attempted: int
    inserted: int
    rejected: int