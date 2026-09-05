from __future__ import annotations

import logging
from datetime import date
from typing import Iterable

from src.graph.ingestion.models import GraphIngestionRelationship
from src.graph.ingestion.repository import GraphIngestionRepository
from src.graph.provenance.models import ProvenanceMetadata
from src.nlp.validation.integration import RelationshipValidationPipeline
from src.nlp.validation.validator import RelationshipCandidate


logger = logging.getLogger(__name__)


class GraphIngestionPipeline:
    """
    Validate extracted graph relationships, attach provenance,
    and persist valid relationships into Neo4j.
    """

    def __init__(
        self,
        repository: GraphIngestionRepository,
        validator: RelationshipValidationPipeline | None = None,
    ) -> None:
        self.repository = repository
        self.validator = validator or RelationshipValidationPipeline()

    def ingest(
        self,
        candidates: Iterable[RelationshipCandidate],
        *,
        source: str,
        source_document: str,
        extraction_method: str = "spacy_triplet",
        confidence: float = 1.0,
        source_url: str | None = None,
        filing_date: date | None = None,
    ) -> dict[str, int]:

        candidates = list(candidates)

        validation_result = self.validator.process(candidates)

        inserted = 0

        for validated in validation_result.valid:

            provenance = ProvenanceMetadata(
                source=source,
                source_document=source_document,
                source_url=source_url,
                filing_date=filing_date,
                extraction_method=extraction_method,
                confidence=confidence,
            )

            graph_relationship = GraphIngestionRelationship(
                subject=validated.subject,
                subject_type=validated.subject_type,
                relationship=validated.relationship,
                object=validated.object,
                object_type=validated.object_type,
                provenance=provenance,
            )

            self.repository.save_relationship(
                graph_relationship
            )

            inserted += 1

            logger.info(
                "Inserted relationship: %s -[%s]-> %s",
                validated.subject,
                validated.relationship,
                validated.object,
            )

        for rejected in validation_result.rejected:
            logger.warning(
                "Rejected relationship: %s -[%s]-> %s | reason=%s",
                rejected.candidate.subject,
                rejected.candidate.relationship,
                rejected.candidate.object,
                rejected.reason,
            )

        return {
            "attempted": len(candidates),
            "inserted": inserted,
            "rejected": len(validation_result.rejected),
        }