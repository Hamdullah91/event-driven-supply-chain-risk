from __future__ import annotations

from datetime import date

from src.graph.ingestion.pipeline import GraphIngestionPipeline
from src.graph.ingestion.resolution import resolve_graph_candidates
from src.nlp.relation_extraction import RelationExtractor
from src.nlp.triplet_extractor import GraphCandidate


class SECGraphIngestionService:
    """
    End-to-end NLP-to-Neo4j ingestion service.

    Text
        -> Entity-first relation extraction
        -> Entity resolution
        -> Ontology validation
        -> Provenance
        -> Neo4j
    """

    def __init__(
        self,
        relation_extractor: RelationExtractor,
        graph_pipeline: GraphIngestionPipeline,
    ) -> None:
        self.relation_extractor = relation_extractor
        self.graph_pipeline = graph_pipeline

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
        source_url: str | None = None,
        filing_date: date | None = None,
    ) -> dict[str, int]:

        # 1. Extract evidence-rich relation candidates using the validated
        #    entity-first SEC relation extractor.
        relation_candidates = self.relation_extractor.extract(text)
        graph_candidates = [
            self._to_graph_candidate(candidate)
            for candidate in relation_candidates
        ]

        # 2. Resolve raw company names to canonical graph entities.
        resolved_candidates = resolve_graph_candidates(
            graph_candidates,
            filing_company=filing_company,
        )

        # 3. Validate + attach provenance + persist to Neo4j.
        return self.graph_pipeline.ingest(
            resolved_candidates,
            source="SEC_EDGAR",
            source_document=source_document,
            source_url=source_url,
            filing_date=filing_date,
            extraction_method="spacy_dependency",
        )
