from __future__ import annotations

import io
import os
import zipfile
from datetime import date

import httpx

from ..models import (
    Company,
    CompanySourceBinding,
    DocumentFamily,
    RawArtifact,
    RemoteDocument,
)
from .base import DisclosureProvider


class OpenDARTDisclosureProvider(DisclosureProvider):
    """South Korea Financial Supervisory Service OpenDART adapter.

    The adapter handles discovery/download only. XML parsing and downstream NLP
    remain source-independent.
    """

    provider_id = "opendart"
    base_url = "https://opendart.fss.or.kr/api"

    def __init__(
        self,
        *,
        api_key: str | None = None,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self.api_key = api_key or os.getenv("OPENDART_API_KEY")
        self._owns_client = client is None
        self.client = client or httpx.AsyncClient(timeout=30.0)

    def supports(
        self,
        company: Company,
        binding: CompanySourceBinding | None,
    ) -> bool:
        return bool(
            binding
            and binding.source_id == self.provider_id
            and binding.external_company_id
        )

    async def close(self) -> None:
        if self._owns_client:
            await self.client.aclose()

    def _require_key(self) -> str:
        if not self.api_key:
            raise RuntimeError(
                "OpenDART requires OPENDART_API_KEY (or api_key=...)"
            )
        return self.api_key

    async def discover_documents(
        self,
        company: Company,
        binding: CompanySourceBinding | None,
        *,
        year_from: int | None = None,
        year_to: int | None = None,
    ) -> list[RemoteDocument]:
        if not binding or not binding.external_company_id:
            raise ValueError(
                f"No OpenDART corp_code configured for {company.company_id}"
            )

        current_year = date.today().year
        start_year = year_from or current_year - 2
        end_year = year_to or current_year
        params = {
            "crtfc_key": self._require_key(),
            "corp_code": binding.external_company_id,
            "bgn_de": f"{start_year}0101",
            "end_de": f"{end_year}1231",
            "pblntf_ty": "A",
            "page_count": 100,
        }
        response = await self.client.get(f"{self.base_url}/list.json", params=params)
        response.raise_for_status()
        payload = response.json()

        status = payload.get("status")
        if status not in {"000", "013"}:
            raise RuntimeError(
                f"OpenDART discovery failed status={status} message={payload.get('message')}"
            )
        if status == "013":
            return []

        documents: list[RemoteDocument] = []
        for row in payload.get("list", []):
            report_name = str(row.get("report_nm", ""))
            normalized_name = report_name.lower()
            if "사업보고서" not in report_name and "annual report" not in normalized_name:
                continue

            receipt_number = str(row["rcept_no"])
            receipt_date = date.fromisoformat(
                f"{row['rcept_dt'][:4]}-{row['rcept_dt'][4:6]}-{row['rcept_dt'][6:8]}"
            )
            documents.append(
                RemoteDocument(
                    source_id=self.provider_id,
                    provider_document_id=receipt_number,
                    company_id=company.company_id,
                    document_family=DocumentFamily.BUSINESS_REPORT,
                    native_document_type=report_name,
                    title=report_name,
                    source_url=(
                        f"{self.base_url}/document.xml?rcept_no={receipt_number}"
                    ),
                    filing_date=receipt_date,
                    publication_date=receipt_date,
                    reporting_year=receipt_date.year - 1,
                    language=binding.metadata.get("language", "ko"),
                    metadata={"corp_code": binding.external_company_id},
                )
            )

        documents.sort(
            key=lambda item: item.filing_date or date.min,
            reverse=True,
        )
        return documents

    async def fetch_document(self, document: RemoteDocument) -> RawArtifact:
        params = {
            "crtfc_key": self._require_key(),
            "rcept_no": document.provider_document_id,
        }
        response = await self.client.get(
            f"{self.base_url}/document.xml",
            params=params,
        )
        response.raise_for_status()
        content = response.content

        # OpenDART's original-document endpoint returns a ZIP archive of XML
        # documents. Normalize that transport detail here while leaving XML
        # parsing to the common format normalizer.
        if content[:2] == b"PK":
            with zipfile.ZipFile(io.BytesIO(content)) as archive:
                xml_names = [
                    name for name in archive.namelist()
                    if name.lower().endswith((".xml", ".xhtml", ".html", ".htm"))
                ]
                if not xml_names:
                    raise RuntimeError("OpenDART archive contains no parseable document")
                selected = max(xml_names, key=lambda name: archive.getinfo(name).file_size)
                content = archive.read(selected)

        return RawArtifact(
            metadata=document,
            content=content,
            mime_type="application/xml",
            response_headers={
                key: value for key, value in response.headers.items()
                if key.lower() in {"content-type", "etag", "last-modified"}
            },
        )
