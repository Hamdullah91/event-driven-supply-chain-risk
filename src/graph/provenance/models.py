from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Literal

from pydantic import BaseModel, Field


ExtractionMethod = Literal[
    "spacy_triplet",
    "spacy_dependency",
    "manual_seed",
    "rule_based",
]


class ProvenanceMetadata(BaseModel):
    source: str = Field(min_length=1)
    source_document: str = Field(min_length=1)
    source_url: str | None = None
    filing_date: date | None = None

    extraction_method: ExtractionMethod

    confidence: float = Field(
        ge=0.0,
        le=1.0,
    )

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )


class ExtractedRelationship(BaseModel):
    source_entity: str = Field(min_length=1)
    relationship_type: str = Field(min_length=1)
    target_entity: str = Field(min_length=1)

    provenance: ProvenanceMetadata