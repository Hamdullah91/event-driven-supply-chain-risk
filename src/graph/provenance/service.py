from __future__ import annotations

from typing import Any

from .models import ProvenanceMetadata


def provenance_to_neo4j(
    provenance: ProvenanceMetadata,
) -> dict[str, Any]:
    """Convert provenance metadata into Neo4j-compatible properties."""

    return {
        "source": provenance.source,
        "source_document": provenance.source_document,
        "source_url": provenance.source_url,
        "filing_date": (
            provenance.filing_date.isoformat()
            if provenance.filing_date
            else None
        ),
        "extraction_method": provenance.extraction_method,
        "confidence": provenance.confidence,
        "created_at": provenance.created_at.isoformat(),
    }
