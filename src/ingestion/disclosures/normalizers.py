from __future__ import annotations

import json
import re
from abc import ABC, abstractmethod
from hashlib import sha256

from bs4 import BeautifulSoup

from .models import (
    DocumentFamily,
    NormalizedDisclosure,
    NormalizedSection,
    RawArtifact,
)


_ROLE_PATTERNS: list[tuple[str, tuple[str, ...]]] = [
    ("RISK_FACTORS", ("risk factor", "principal risk", "key risk")),
    ("SUPPLY_CHAIN", ("supply chain", "supplier", "procurement", "sourcing")),
    ("MATERIALS", ("raw material", "materials", "commodit")),
    ("MANUFACTURING", ("manufactur", "production", "capacity")),
    ("FACILITIES", ("facilit", "properties", "plants", "sites")),
    ("PRODUCTS", ("products", "services", "portfolio")),
    ("CUSTOMERS", ("customer", "sales", "orders")),
    ("GEOGRAPHY", ("geograph", "regions", "markets")),
    ("MD_AND_A", ("management discussion", "operating review", "financial review")),
    ("BUSINESS", ("business", "operations", "company overview")),
]


def semantic_role(heading: str | None) -> str | None:
    if not heading:
        return None
    normalized = re.sub(r"\s+", " ", heading.strip().lower())
    for role, patterns in _ROLE_PATTERNS:
        if any(pattern in normalized for pattern in patterns):
            return role
    return "OTHER"


def _document_id(artifact: RawArtifact) -> str:
    metadata = artifact.metadata
    identity = "|".join(
        [
            metadata.company_id,
            metadata.document_family.value if metadata.document_family else "unknown",
            str(metadata.reporting_period_end or metadata.reporting_year or "unknown"),
        ]
    )
    return sha256(identity.encode("utf-8")).hexdigest()[:32]


def _representation_id(artifact: RawArtifact) -> str:
    return sha256(artifact.content).hexdigest()


class DisclosureNormalizer(ABC):
    @abstractmethod
    def supports(self, artifact: RawArtifact) -> bool:
        raise NotImplementedError

    @abstractmethod
    def normalize(self, artifact: RawArtifact) -> NormalizedDisclosure:
        raise NotImplementedError

    def _build(
        self,
        artifact: RawArtifact,
        *,
        full_text: str,
        sections: list[NormalizedSection],
    ) -> NormalizedDisclosure:
        metadata = artifact.metadata
        family = metadata.document_family or DocumentFamily.OTHER_ANNUAL_DISCLOSURE
        return NormalizedDisclosure(
            document_id=_document_id(artifact),
            company_id=metadata.company_id,
            source_id=metadata.source_id,
            title=metadata.title,
            document_family=family,
            native_document_type=metadata.native_document_type,
            reporting_period_end=metadata.reporting_period_end,
            reporting_year=metadata.reporting_year,
            filing_date=metadata.filing_date,
            publication_date=metadata.publication_date,
            language=metadata.language or "en",
            sections=sections,
            full_text=full_text.strip(),
            source_representation_id=_representation_id(artifact),
            metadata=metadata.metadata,
        )


class HTMLNormalizer(DisclosureNormalizer):
    def supports(self, artifact: RawArtifact) -> bool:
        mime = artifact.mime_type.lower()
        return "html" in mime or artifact.metadata.source_url.lower().endswith((".html", ".htm", ".xhtml"))

    def normalize(self, artifact: RawArtifact) -> NormalizedDisclosure:
        soup = BeautifulSoup(artifact.content, "lxml")
        for tag in soup(["script", "style", "noscript"]):
            tag.decompose()

        sections: list[NormalizedSection] = []
        current_heading: str | None = None
        buffer: list[str] = []

        def flush() -> None:
            nonlocal buffer
            text = "\n".join(part for part in buffer if part).strip()
            if text:
                sections.append(
                    NormalizedSection(
                        native_heading=current_heading,
                        semantic_role=semantic_role(current_heading),
                        text=text,
                        order=len(sections),
                    )
                )
            buffer = []

        for node in soup.find_all(["h1", "h2", "h3", "h4", "p", "li"]):
            text = " ".join(node.stripped_strings)
            if not text:
                continue
            if node.name in {"h1", "h2", "h3", "h4"}:
                flush()
                current_heading = text
            else:
                buffer.append(text)
        flush()

        if not sections:
            text = soup.get_text("\n", strip=True)
            sections = [NormalizedSection(text=text, order=0)]
        full_text = "\n\n".join(section.text for section in sections)
        return self._build(artifact, full_text=full_text, sections=sections)


class XMLNormalizer(DisclosureNormalizer):
    def supports(self, artifact: RawArtifact) -> bool:
        mime = artifact.mime_type.lower()
        return "xml" in mime or artifact.metadata.source_url.lower().endswith(".xml")

    def normalize(self, artifact: RawArtifact) -> NormalizedDisclosure:
        soup = BeautifulSoup(artifact.content, "xml")
        text = soup.get_text("\n", strip=True)
        sections = [NormalizedSection(text=text, order=0)]
        return self._build(artifact, full_text=text, sections=sections)


class JSONNormalizer(DisclosureNormalizer):
    def supports(self, artifact: RawArtifact) -> bool:
        return "json" in artifact.mime_type.lower()

    def normalize(self, artifact: RawArtifact) -> NormalizedDisclosure:
        payload = json.loads(artifact.content.decode("utf-8"))
        text = json.dumps(payload, ensure_ascii=False, indent=2)
        sections = [NormalizedSection(text=text, order=0)]
        return self._build(artifact, full_text=text, sections=sections)


class PDFNormalizer(DisclosureNormalizer):
    def supports(self, artifact: RawArtifact) -> bool:
        return "pdf" in artifact.mime_type.lower() or artifact.metadata.source_url.lower().endswith(".pdf")

    def normalize(self, artifact: RawArtifact) -> NormalizedDisclosure:
        try:
            import fitz  # PyMuPDF
        except ImportError as exc:  # pragma: no cover - environment guard
            raise RuntimeError(
                "PDF normalization requires PyMuPDF. Install requirements.txt."
            ) from exc

        document = fitz.open(stream=artifact.content, filetype="pdf")
        sections: list[NormalizedSection] = []
        page_texts: list[str] = []
        for page_index, page in enumerate(document):
            text = page.get_text("text").strip()
            if not text:
                continue
            page_texts.append(text)
            sections.append(
                NormalizedSection(
                    native_heading=f"Page {page_index + 1}",
                    text=text,
                    order=len(sections),
                    page_start=page_index + 1,
                    page_end=page_index + 1,
                )
            )
        document.close()
        full_text = "\n\n".join(page_texts)
        if not full_text.strip():
            raise RuntimeError("PDF contains no extractable text; OCR is not enabled")
        return self._build(artifact, full_text=full_text, sections=sections)


class NormalizerRegistry:
    def __init__(self, normalizers: list[DisclosureNormalizer] | None = None) -> None:
        self.normalizers = normalizers or [
            HTMLNormalizer(),
            XMLNormalizer(),
            JSONNormalizer(),
            PDFNormalizer(),
        ]

    def normalize(self, artifact: RawArtifact) -> NormalizedDisclosure:
        for normalizer in self.normalizers:
            if normalizer.supports(artifact):
                return normalizer.normalize(artifact)
        raise ValueError(f"No normalizer available for MIME type {artifact.mime_type!r}")
