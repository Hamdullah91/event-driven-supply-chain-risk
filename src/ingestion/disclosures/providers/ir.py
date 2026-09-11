from __future__ import annotations

import re
from datetime import date
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup

from ..http import get_with_retries
from ..models import (
    Company,
    CompanySourceBinding,
    DocumentFamily,
    RawArtifact,
    RemoteDocument,
)
from .base import DisclosureProvider


_YEAR_RE = re.compile(r"\b(20\d{2})\b")


class InvestorRelationsDisclosureProvider(DisclosureProvider):
    """Restricted fallback crawler for explicitly configured official IR pages.

    This is intentionally not a general web crawler. Discovery is restricted to
    the configured official domain and a shallow traversal depth.
    """

    provider_id = "investor_relations"

    def __init__(
        self,
        *,
        client: httpx.AsyncClient | None = None,
        max_depth: int = 1,
        max_pages: int = 12,
    ) -> None:
        self._owns_client = client is None
        self.client = client or httpx.AsyncClient(
            timeout=30.0,
            follow_redirects=True,
            headers={"User-Agent": "SupplyChainRiskResearch/1.0"},
        )
        self.max_depth = max_depth
        self.max_pages = max_pages

    async def close(self) -> None:
        if self._owns_client:
            await self.client.aclose()

    def supports(
        self,
        company: Company,
        binding: CompanySourceBinding | None,
    ) -> bool:
        return bool(
            binding
            and binding.source_id == self.provider_id
            and binding.discovery_url
        )

    @staticmethod
    def _same_domain(root_url: str, candidate_url: str) -> bool:
        root_host = (urlparse(root_url).hostname or "").lower()
        candidate_host = (urlparse(candidate_url).hostname or "").lower()
        return bool(root_host and candidate_host and root_host == candidate_host)

    @staticmethod
    def _score_candidate(text: str, href: str, target_years: set[int]) -> int:
        haystack = f"{text} {href}".lower()
        score = 0
        if "annual report" in haystack or "annual-report" in haystack:
            score += 45
        if "integrated report" in haystack or "integrated-report" in haystack:
            score += 35
        if "universal registration document" in haystack:
            score += 40
        if href.lower().endswith(".pdf"):
            score += 25
        if "/invest" in haystack or "/report" in haystack or "/financial" in haystack:
            score += 10
        if any(str(year) in haystack for year in target_years):
            score += 25
        if "sustainability" in haystack and "annual report" not in haystack:
            score -= 40
        if "quarter" in haystack or "half-year" in haystack or "presentation" in haystack:
            score -= 50
        return score

    @staticmethod
    def _family(text: str, href: str) -> DocumentFamily:
        haystack = f"{text} {href}".lower()
        if "integrated report" in haystack:
            return DocumentFamily.INTEGRATED_REPORT
        if "universal registration document" in haystack:
            return DocumentFamily.UNIVERSAL_REGISTRATION_DOCUMENT
        return DocumentFamily.ANNUAL_REPORT

    async def discover_documents(
        self,
        company: Company,
        binding: CompanySourceBinding | None,
        *,
        year_from: int | None = None,
        year_to: int | None = None,
    ) -> list[RemoteDocument]:
        if not binding or not binding.discovery_url:
            raise ValueError(
                f"No official IR discovery URL configured for {company.company_id}"
            )

        current_year = date.today().year
        years = set(range(year_from or current_year - 2, (year_to or current_year) + 1))
        root_url = binding.discovery_url
        queue: list[tuple[str, int]] = [(root_url, 0)]
        visited: set[str] = set()
        candidates: dict[str, tuple[int, str, DocumentFamily, int | None]] = {}

        while queue and len(visited) < self.max_pages:
            page_url, depth = queue.pop(0)
            if page_url in visited:
                continue
            visited.add(page_url)

            response = await get_with_retries(self.client, page_url)
            soup = BeautifulSoup(response.text, "html.parser")

            for anchor in soup.find_all("a", href=True):
                text = " ".join(anchor.stripped_strings)
                absolute = urljoin(str(response.url), anchor["href"])
                if not self._same_domain(root_url, absolute):
                    continue

                score = self._score_candidate(text, absolute, years)
                match = _YEAR_RE.search(f"{text} {absolute}")
                report_year = int(match.group(1)) if match else None
                if score >= 35:
                    candidates[absolute] = (
                        score,
                        text or company.legal_name,
                        self._family(text, absolute),
                        report_year,
                    )

                parsed_path = urlparse(absolute).path.lower()
                if (
                    depth < self.max_depth
                    and not parsed_path.endswith((".pdf", ".zip", ".xml"))
                    and any(
                        token in parsed_path
                        for token in ("invest", "report", "financial", "result")
                    )
                    and absolute not in visited
                ):
                    queue.append((absolute, depth + 1))

        documents = [
            RemoteDocument(
                source_id=self.provider_id,
                company_id=company.company_id,
                document_family=family,
                native_document_type=family.value,
                title=title,
                source_url=url,
                reporting_year=report_year,
                language=(
                    binding.preferred_languages
                    or company.preferred_languages
                    or ["en"]
                )[0],
                metadata={
                    "discovery_url": root_url,
                    "candidate_score": score,
                },
            )
            for url, (score, title, family, report_year) in candidates.items()
            if report_year is None or report_year in years
        ]
        documents.sort(
            key=lambda item: (
                int(item.metadata.get("candidate_score", 0)),
                item.reporting_year or 0,
            ),
            reverse=True,
        )
        return documents

    async def fetch_document(self, document: RemoteDocument) -> RawArtifact:
        response = await get_with_retries(self.client, document.source_url)
        mime_type = response.headers.get("content-type", "").split(";")[0].strip()
        if not mime_type:
            mime_type = (
                "application/pdf"
                if document.source_url.lower().endswith(".pdf")
                else "text/html"
            )
        return RawArtifact(
            metadata=document,
            content=response.content,
            mime_type=mime_type,
            response_headers={
                key: value
                for key, value in response.headers.items()
                if key.lower() in {"content-type", "etag", "last-modified"}
            },
        )
