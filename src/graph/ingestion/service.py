from __future__ import annotations

from datetime import date

from src.graph.ingestion.pipeline import GraphIngestionPipeline
from src.graph.ingestion.resolution import resolve_graph_candidates
from src.nlp.triplet_extractor import TripletExtractor


class SECGraphIngestionService:
    """
    End-to-end NLP-to-Neo4j ingestion service.

    Text
        -> Triplet extraction
        -> Entity resolution
        -> Ontology validation
        -> Provenance
        -> Neo4j
    """

    def __init__(
        self,
        triplet_extractor: TripletExtractor,
        graph_pipeline: GraphIngestionPipeline,
    ) -> None:
        self.triplet_extractor = triplet_extractor
        self.graph_pipeline = graph_pipeline

    def ingest_text(
        self,
        text: str,
        *,
        filing_company: str,
        source_document: str,
        source_url: str | None = None,
        filing_date: date | None = None,
    ) -> dict[str, int]:

        # 1. Extract raw SPO graph candidates
        graph_candidates = self.triplet_extractor.extract(text)

        # 2. Resolve raw company names to canonical entities
        resolved_candidates = resolve_graph_candidates(
            graph_candidates,
            filing_company=filing_company,
        )

        # 3. Validate + attach provenance + persist to Neo4j
        return self.graph_pipeline.ingest(
            resolved_candidates,
            source="SEC_EDGAR",
            source_document=source_document,
            source_url=source_url,
            filing_date=filing_date,
            extraction_method="spacy_triplet",
        )