from __future__ import annotations

from datetime import date

from src.graph.ingestion.pipeline import GraphIngestionPipeline
from src.graph.ingestion.resolution import resolve_graph_candidates
from src.nlp.relation_extraction import RelationExtractor
from src.nlp.triplet_extractor import GraphCandidate


class DisclosureGraphIngestionService:
    """Source-independent NLP-to-Neo4j relationship ingestion service.

    Text
        -> Entity-first relation extraction
        -> Entity resolution
        -> Ontology validation
        -> Provenance
        -> Neo4j

    Source acquisition/normalization happens upstream. This service only needs
    normalized text plus provenance metadata.
    """

    def __init__(
        self,
        relation_extractor: RelationExtractor,
        graph_pipeline: GraphIngestionPipeline,
        *,
        default_source: str = "CORPORATE_DISCLOSURE",
    ) -> None:
        self.relation_extractor = relation_extractor
        self.graph_pipeline = graph_pipeline
        self.default_source = default_source

    @staticmethod
    def _to_graph_candidate(candidate) -> GraphCandidate:
        return GraphCandidate(
            subject=candidate.subject,
            predicate=candidate.relationship,
            object=candidate.object,
            source_sentence=candidate.source_sentence,
            subject_type=candidate.subject_type,
            object_type=candidate.object_type,
        )

    def ingest_text(
        self,
        text: str,
        *,
        filing_company: str,
        source_document: str,
        source: str | None = None,
        source_url: str | None = None,
        filing_date: date | None = None,
        extraction_method: str = "spacy_dependency",
    ) -> dict[str, int]:
        relation_candidates = self.relation_extractor.extract(text)
        graph_candidates = [
            self._to_graph_candidate(candidate)
            for candidate in relation_candidates
        ]

        resolved_candidates = resolve_graph_candidates(
            graph_candidates,
            filing_company=filing_company,
        )

        return self.graph_pipeline.ingest(
            resolved_candidates,
            source=source or self.default_source,
            source_document=source_document,
            source_url=source_url,
            filing_date=filing_date,
            extraction_method=extraction_method,
        )


class SECGraphIngestionService(DisclosureGraphIngestionService):
    """Backward-compatible SEC specialization used by existing scripts/tests."""

    def __init__(
        self,
        relation_extractor: RelationExtractor,
        graph_pipeline: GraphIngestionPipeline,
    ) -> None:
        super().__init__(
            relation_extractor=relation_extractor,
            graph_pipeline=graph_pipeline,
            default_source="SEC_EDGAR",
        )
