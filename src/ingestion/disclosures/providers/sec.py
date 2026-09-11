from __future__ import annotations

import mimetypes
from datetime import date

from src.ingestion.sec.client import SECClient
from src.ingestion.sec.crawler import (
    FilingNotFoundError,
    build_archive_url,
    find_latest_form_with_history,
)
from src.ingestion.sec.models import CompanyTarget

from ..models import (
    Company,
    CompanySourceBinding,
    DocumentFamily,
    RawArtifact,
    RemoteDocument,
)
from .base import DisclosureProvider


_FORM_TO_FAMILY = {
    "10-K": DocumentFamily.TEN_K,
    "20-F": DocumentFamily.TWENTY_F,
}
_FAMILY_TO_FORM = {value: key for key, value in _FORM_TO_FAMILY.items()}


class SECDisclosureProvider(DisclosureProvider):
    provider_id = "sec_edgar"

    def __init__(self, client: SECClient) -> None:
        self.client = client

    def supports(
        self,
        company: Company,
        binding: CompanySourceBinding | None,
    ) -> bool:
        return bool(
            (binding and binding.source_id == self.provider_id)
            or company.identifier("SEC_CIK")
        )

    def _cik(
        self,
        company: Company,
        binding: CompanySourceBinding | None,
    ) -> str:
        value = (
            binding.external_company_id
            if binding and binding.external_company_id
            else company.identifier("SEC_CIK")
        )
        if not value:
            raise ValueError(f"No SEC CIK configured for {company.company_id}")
        return str(value).zfill(10)

    async def discover_documents(
        self,
        company: Company,
        binding: CompanySourceBinding | None,
        *,
        year_from: int | None = None,
        year_to: int | None = None,
    ) -> list[RemoteDocument]:
        cik = self._cik(company, binding)
        target = CompanyTarget(name=company.legal_name, cik=cik)
        submissions = await self.client.get_company_submissions(cik)

        configured_family = None
        if binding:
            raw_family = binding.metadata.get("document_family")
            if raw_family:
                configured_family = DocumentFamily(raw_family)

        families = (
            [configured_family]
            if configured_family is not None
            else [DocumentFamily.TEN_K, DocumentFamily.TWENTY_F]
        )

        discovered: list[RemoteDocument] = []
        for family in families:
            form = _FAMILY_TO_FORM.get(family)
            if form is None:
                continue
            try:
                filing = await find_latest_form_with_history(
                    client=self.client,
                    submissions=submissions,
                    form=form,
                )
            except FilingNotFoundError:
                continue

            filing_date = date.fromisoformat(filing["filing_date"])
            if year_from is not None and filing_date.year < year_from:
                continue
            if year_to is not None and filing_date.year > year_to:
                continue

            source_url = build_archive_url(
                company=target,
                accession_number=filing["accession_number"],
                primary_document=filing["primary_document"],
            )
            report_date = (
                date.fromisoformat(filing["report_date"])
                if filing.get("report_date")
                else None
            )
            discovered.append(
                RemoteDocument(
                    source_id=self.provider_id,
                    provider_document_id=filing["accession_number"],
                    company_id=company.company_id,
                    document_family=family,
                    native_document_type=form,
                    title=f"{company.legal_name} {form}",
                    source_url=source_url,
                    filing_date=filing_date,
                    publication_date=filing_date,
                    reporting_period_end=report_date,
                    reporting_year=(
                        report_date.year if report_date else filing_date.year
                    ),
                    language="en",
                    metadata={
                        "cik": cik,
                        "primary_document": filing["primary_document"],
                    },
                )
            )

        return discovered

    async def fetch_document(self, document: RemoteDocument) -> RawArtifact:
        content = await self.client.get_bytes(document.source_url)
        mime_type = mimetypes.guess_type(document.source_url)[0] or "text/html"
        return RawArtifact(
            metadata=document,
            content=content,
            mime_type=mime_type,
        )
