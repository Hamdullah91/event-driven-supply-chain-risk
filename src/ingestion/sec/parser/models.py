from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class FilingMetadata:
    cik: str
    accession_number: str
    company_name: str
    filing_date: str
    form: str
    source_url: str


@dataclass(frozen=True, slots=True)
class FilingParagraph:
    paragraph_id: str
    section: str
    section_title: str
    paragraph_index: int
    text: str
    relevant: bool
    matched_keywords: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        result = asdict(self)
        result["matched_keywords"] = list(self.matched_keywords)
        return result


@dataclass(frozen=True, slots=True)
class FilingSection:
    item: str
    title: str
    text: str
    paragraphs: tuple[FilingParagraph, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "item": self.item,
            "title": self.title,
            "text": self.text,
            "paragraphs": [
                paragraph.to_dict()
                for paragraph in self.paragraphs
            ],
        }


@dataclass(frozen=True, slots=True)
class ParsedFiling:
    metadata: FilingMetadata
    sections: tuple[FilingSection, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "metadata": asdict(self.metadata),
            "sections": [
                section.to_dict()
                for section in self.sections
            ],
        }