from __future__ import annotations

from datetime import date

from src.graph.ingestion.service import DisclosureGraphIngestionService
from src.ingestion.sec.preprocessing.chunker import TextChunker

from .models import NormalizedDisclosure
from .registry import CompanyRegistry


class NormalizedDisclosureGraphBridge:
    """Feeds normalized English disclosure text into the existing NLP graph path."""

    def __init__(
        self,
        *,
        company_registry: CompanyRegistry,
        graph_service: DisclosureGraphIngestionService,
        chunker: TextChunker | None = None,
    ) -> None:
        self.company_registry = company_registry
        self.graph_service = graph_service
        self.chunker = chunker or TextChunker()

    def ingest(self, disclosure: NormalizedDisclosure) -> dict[str, int]:
        language = (disclosure.language or "").lower().split("-")[0]
        if language != "en":
            return {"attempted": 0, "inserted": 0, "rejected": 0}

        company = self.company_registry.get(disclosure.company_id)
        filing_date: date | None = disclosure.filing_date or disclosure.publication_date
        source_document = disclosure.metadata.get("provider_document_id")
        if not source_document:
            source_document = disclosure.source_representation_id

        totals = {"attempted": 0, "inserted": 0, "rejected": 0}
        sections = disclosure.sections or []
        texts = [section.text for section in sections if section.text.strip()]
        if not texts and disclosure.full_text.strip():
            texts = [disclosure.full_text]

        for text in texts:
            for chunk in self.chunker.split(text):
                result = self.graph_service.ingest_text(
                    chunk,
                    filing_company=company.legal_name,
                    source_document=str(source_document),
                    source=disclosure.source_id.upper(),
                    source_url=disclosure.metadata.get("source_url"),
                    filing_date=filing_date,
                )
                for key in totals:
                    totals[key] += result[key]
        return totals
