from typing import Iterable

from .models import ResolvedEntity
from .resolver import resolve_companies
from src.graph.provenance.models import (
    ExtractedRelationship,
    ProvenanceMetadata,
)

def resolve_extracted_companies(
    company_names: Iterable[str],
) -> list[ResolvedEntity]:
    """
    Resolve company names produced by the NLP entity extractor.

    Duplicate raw names are removed before resolution.
    """
    unique_names = list(dict.fromkeys(company_names))

    return resolve_companies(unique_names)

def get_resolution_stats(
    results: list[ResolvedEntity],
) -> dict[str, int | float]:
    total = len(results)

    resolved = sum(
        1 for result in results
        if result.canonical_id is not None
    )

    unresolved = total - resolved

    resolution_rate = resolved / total if total else 0.0

    return {
        "total": total,
        "resolved": resolved,
        "unresolved": unresolved,
        "resolution_rate": resolution_rate,
    }

def build_provenanced_relationship(
    source_entity: str,
    relationship_type: str,
    target_entity: str,
    *,
    source: str,
    source_document: str,
    extraction_method: str,
    confidence: float,
    source_url: str | None = None,
    filing_date=None,
) -> ExtractedRelationship:
    """
    Build a resolved relationship while preserving extraction provenance.
    """

    return ExtractedRelationship(
        source_entity=source_entity,
        relationship_type=relationship_type,
        target_entity=target_entity,
        provenance=ProvenanceMetadata(
            source=source,
            source_document=source_document,
            source_url=source_url,
            filing_date=filing_date,
            extraction_method=extraction_method,
            confidence=confidence,
        ),
    )