from __future__ import annotations
from importlib.metadata import metadata

from src.ingestion.sec.parser.models import ParsedFiling

from .chunker import TextChunker
from .cleaner import FilingTextCleaner
from .models import (
    ChunkMetadata,
    FilingChunk,
    FilingSection,
    ProcessedFiling,
)


class FilingPreprocessor:
    def __init__(self) -> None:
        self.cleaner = FilingTextCleaner()
        self.chunker = TextChunker()

    def process(
        self,
        parsed_filing: ParsedFiling,
    ) -> ProcessedFiling:

        metadata = parsed_filing.metadata

        filing = ProcessedFiling(
            cik=metadata.cik,
            company_name=metadata.company_name,
            accession_number=metadata.accession_number,
            filing_date=metadata.filing_date,
            form_type=metadata.form,
            source_url=metadata.source_url,
        )

        for parsed_section in parsed_filing.sections:

            cleaned_text = self.cleaner.clean(
                parsed_section.text
            )

            chunks = self.chunker.split(
                cleaned_text
            )

            section = FilingSection(
                item_number=parsed_section.item,
                title=parsed_section.title,
                text=cleaned_text,
            )

            for index, chunk_text in enumerate(chunks):

                chunk_metadata = ChunkMetadata(
                    cik=metadata.cik,
                    company_name=metadata.company_name,
                    accession_number=metadata.accession_number,
                    filing_date=metadata.filing_date,
                    form_type=metadata.form,
                    section=parsed_section.item,
                    section_title=parsed_section.title,
                    source_url=metadata.source_url,
                )

                chunk = FilingChunk(
                    chunk_id=(
                        f"{metadata.accession_number}_"
                        f"{parsed_section.item}_{index}"
                    ),
                    text=chunk_text,
                    chunk_index=index,
                    metadata=chunk_metadata,
                )

                section.chunks.append(chunk)

            filing.sections.append(section)

        return filing