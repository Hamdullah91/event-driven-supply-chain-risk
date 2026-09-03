from __future__ import annotations

from dataclasses import asdict, dataclass, field


@dataclass(slots=True, frozen=True)
class ChunkMetadata:
    cik: str
    company_name: str
    accession_number: str
    filing_date: str
    form_type: str
    section: str
    section_title: str
    source_url: str


@dataclass(slots=True, frozen=True)
class FilingChunk:
    chunk_id: str
    text: str
    chunk_index: int
    metadata: ChunkMetadata

    @property
    def character_count(self) -> int:
        return len(self.text)

    @property
    def word_count(self) -> int:
        return len(self.text.split())


@dataclass(slots=True)
class FilingSection:
    item_number: str
    title: str
    text: str
    chunks: list[FilingChunk] = field(default_factory=list)


@dataclass(slots=True)
class ProcessedFiling:
    cik: str
    company_name: str
    accession_number: str
    filing_date: str
    form_type: str
    source_url: str
    sections: list[FilingSection] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)