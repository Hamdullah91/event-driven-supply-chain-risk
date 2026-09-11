from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from .models import (
    DisclosureDocument,
    DocumentRepresentation,
    IngestionStatus,
    NormalizedDisclosure,
    RemoteDocument,
)
from .normalizers import NormalizerRegistry
from .registry import CompanyRegistry
from .router import SourceRouter
from .storage import DocumentRegistry, RawArtifactStore


logger = logging.getLogger(__name__)


@dataclass(slots=True)
class IngestionResult:
    company_id: str
    source_id: str
    provider_document_id: str
    status: IngestionStatus
    normalized: NormalizedDisclosure | None = None
    error: Exception | None = None
    duplicate: bool = False


class DisclosureIngestionService:
    def __init__(
        self,
        *,
        company_registry: CompanyRegistry,
        router: SourceRouter,
        artifact_store: RawArtifactStore,
        document_registry: DocumentRegistry,
        normalizers: NormalizerRegistry | None = None,
        supported_languages: set[str] | None = None,
    ) -> None:
        self.company_registry = company_registry
        self.router = router
        self.artifact_store = artifact_store
        self.document_registry = document_registry
        self.normalizers = normalizers or NormalizerRegistry()
        self.supported_languages = supported_languages or {"en"}

    @staticmethod
    def _provider_document_key(document: RemoteDocument) -> str:
        return document.provider_document_id or document.source_url

    @staticmethod
    def _logical_key(document: RemoteDocument) -> str:
        family = document.document_family.value if document.document_family else "other"
        period = document.reporting_period_end or document.reporting_year or "unknown"
        return f"{document.company_id}:{family}:{period}"

    async def ingest_document(
        self,
        *,
        provider,
        document: RemoteDocument,
    ) -> IngestionResult:
        provider_document_id = self._provider_document_key(document)
        self.document_registry.set_status(
            company_id=document.company_id,
            source_id=document.source_id,
            provider_document_id=provider_document_id,
            status=IngestionStatus.DOWNLOADING,
        )

        try:
            artifact = await provider.fetch_document(document)
        except Exception as exc:
            self.document_registry.set_status(
                company_id=document.company_id,
                source_id=document.source_id,
                provider_document_id=provider_document_id,
                status=IngestionStatus.FAILED_DOWNLOAD,
                error=exc,
            )
            return IngestionResult(
                company_id=document.company_id,
                source_id=document.source_id,
                provider_document_id=provider_document_id,
                status=IngestionStatus.FAILED_DOWNLOAD,
                error=exc,
            )

        content_hash, storage_path = self.artifact_store.save(artifact)
        existing = self.document_registry.representation_by_hash(content_hash)
        if existing is not None:
            self.document_registry.set_status(
                company_id=document.company_id,
                source_id=document.source_id,
                provider_document_id=provider_document_id,
                status=IngestionStatus.DOWNLOADED,
            )
            return IngestionResult(
                company_id=document.company_id,
                source_id=document.source_id,
                provider_document_id=provider_document_id,
                status=IngestionStatus.DOWNLOADED,
                duplicate=True,
            )

        self.document_registry.set_status(
            company_id=document.company_id,
            source_id=document.source_id,
            provider_document_id=provider_document_id,
            status=IngestionStatus.DOWNLOADED,
        )

        try:
            normalized = self.normalizers.normalize(artifact)
        except Exception as exc:
            self.document_registry.set_status(
                company_id=document.company_id,
                source_id=document.source_id,
                provider_document_id=provider_document_id,
                status=IngestionStatus.FAILED_NORMALIZATION,
                error=exc,
            )
            return IngestionResult(
                company_id=document.company_id,
                source_id=document.source_id,
                provider_document_id=provider_document_id,
                status=IngestionStatus.FAILED_NORMALIZATION,
                error=exc,
            )

        now = datetime.now(timezone.utc)
        disclosure_document = DisclosureDocument(
            document_id=normalized.document_id,
            company_id=document.company_id,
            document_family=normalized.document_family,
            native_document_type=document.native_document_type,
            reporting_period_end=document.reporting_period_end,
            reporting_year=document.reporting_year,
            publication_date=document.publication_date,
            filing_date=document.filing_date,
            language=document.language,
            logical_document_key=self._logical_key(document),
            current_representation_id=normalized.source_representation_id,
            created_at=now,
            updated_at=now,
        )
        representation = DocumentRepresentation(
            representation_id=normalized.source_representation_id,
            document_id=normalized.document_id,
            source_id=document.source_id,
            provider_document_id=document.provider_document_id,
            source_url=document.source_url,
            retrieved_at=artifact.retrieved_at,
            mime_type=artifact.mime_type,
            content_sha256=content_hash,
            byte_size=len(artifact.content),
            storage_uri=str(storage_path),
            is_canonical_representation=True,
        )
        self.document_registry.upsert_document(disclosure_document)
        self.document_registry.insert_representation(representation)
        self.document_registry.save_normalized(normalized)

        language = (normalized.language or "").lower().split("-")[0]
        status = (
            IngestionStatus.NORMALIZED
            if language in self.supported_languages
            else IngestionStatus.NORMALIZED_UNSUPPORTED_LANGUAGE
        )
        self.document_registry.set_status(
            company_id=document.company_id,
            source_id=document.source_id,
            provider_document_id=provider_document_id,
            status=status,
        )
        return IngestionResult(
            company_id=document.company_id,
            source_id=document.source_id,
            provider_document_id=provider_document_id,
            status=status,
            normalized=normalized,
        )

    async def ingest_company(
        self,
        company_id: str,
        *,
        year_from: int | None = None,
        year_to: int | None = None,
    ) -> list[IngestionResult]:
        company = self.company_registry.get(company_id)
        results: list[IngestionResult] = []

        for provider, binding in self.router.routes_for(company):
            try:
                documents = await provider.discover_documents(
                    company,
                    binding,
                    year_from=year_from,
                    year_to=year_to,
                )
            except Exception as exc:
                self.document_registry.set_status(
                    company_id=company.company_id,
                    source_id=provider.provider_id,
                    provider_document_id="__discovery__",
                    status=IngestionStatus.FAILED_DISCOVERY,
                    error=exc,
                )
                results.append(
                    IngestionResult(
                        company_id=company.company_id,
                        source_id=provider.provider_id,
                        provider_document_id="__discovery__",
                        status=IngestionStatus.FAILED_DISCOVERY,
                        error=exc,
                    )
                )
                continue

            for document in documents:
                self.document_registry.set_status(
                    company_id=company.company_id,
                    source_id=provider.provider_id,
                    provider_document_id=self._provider_document_key(document),
                    status=IngestionStatus.DISCOVERED,
                )
                results.append(
                    await self.ingest_document(
                        provider=provider,
                        document=document,
                    )
                )

        return results

    async def ingest_enabled_companies(
        self,
        *,
        year_from: int | None = None,
        year_to: int | None = None,
        max_concurrency: int = 8,
    ) -> list[IngestionResult]:
        if max_concurrency <= 0:
            raise ValueError("max_concurrency must be greater than zero")
        semaphore = asyncio.Semaphore(max_concurrency)

        async def run(company_id: str) -> list[IngestionResult]:
            async with semaphore:
                try:
                    return await self.ingest_company(
                        company_id,
                        year_from=year_from,
                        year_to=year_to,
                    )
                except Exception as exc:  # defensive isolation
                    logger.exception("Disclosure ingestion failed company=%s", company_id)
                    return [
                        IngestionResult(
                            company_id=company_id,
                            source_id="unknown",
                            provider_document_id="__company__",
                            status=IngestionStatus.FAILED_DISCOVERY,
                            error=exc,
                        )
                    ]

        batches = await asyncio.gather(
            *(run(company.company_id) for company in self.company_registry.enabled())
        )
        return [result for batch in batches for result in batch]
