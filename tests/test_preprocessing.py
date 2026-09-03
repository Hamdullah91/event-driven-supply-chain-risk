from src.ingestion.sec.parser.models import (
    FilingMetadata,
    FilingParagraph,
    FilingSection as ParsedSection,
    ParsedFiling,
)

from src.ingestion.sec.preprocessing import FilingPreprocessor


def test_filing_preprocessor():
    metadata = FilingMetadata(
        cik="0001045810",
        accession_number="0001045810-26-000001",
        company_name="NVIDIA Corporation",
        filing_date="2026-02-25",
        form="10-K",
        source_url="https://www.sec.gov/example",
    )

    paragraph = FilingParagraph(
        paragraph_id="1A-0",
        section="1A",
        section_title="Risk Factors",
        paragraph_index=0,
        text="NVIDIA relies on third-party manufacturers.",
        relevant=True,
        matched_keywords=("manufacturing",),
    )

    section = ParsedSection(
        item="1A",
        title="Risk Factors",
        text="""
        NVIDIA   Corporation relies on third-party manufacturers.

        Manufacturing disruptions may affect our business.
        """,
        paragraphs=(paragraph,),
    )

    parsed_filing = ParsedFiling(
        metadata=metadata,
        sections=(section,),
    )

    processor = FilingPreprocessor()

    filing = processor.process(parsed_filing)

    assert filing.company_name == "NVIDIA Corporation"
    assert filing.filing_date == "2026-02-25"
    assert filing.form_type == "10-K"

    assert len(filing.sections) == 1

    processed_section = filing.sections[0]

    assert processed_section.item_number == "1A"
    assert processed_section.title == "Risk Factors"

    assert len(processed_section.chunks) >= 1

    chunk = processed_section.chunks[0]

    assert "NVIDIA Corporation" in chunk.text
    assert chunk.metadata.cik == "0001045810"
    assert chunk.metadata.section == "1A"
    assert chunk.metadata.section_title == "Risk Factors"


from src.ingestion.sec.preprocessing import TextChunker


def test_text_chunker_creates_multiple_chunks():
    text = "NVIDIA depends on semiconductor suppliers. " * 200

    chunker = TextChunker(
        chunk_size=500,
        overlap=100,
    )

    chunks = chunker.split(text)

    assert len(chunks) > 1

    assert len(chunks[0]) <= 500


from src.ingestion.sec.preprocessing import FilingTextCleaner


def test_text_cleaner_normalizes_text():
    cleaner = FilingTextCleaner()

    messy_text = (
        "NVIDIA\xa0   Corporation\r\n\r\n\r\n"
        "depends\t\t on suppliers."
    )

    cleaned = cleaner.clean(messy_text)

    assert "\xa0" not in cleaned
    assert "\t" not in cleaned
    assert "\r" not in cleaned
    assert "NVIDIA Corporation" in cleaned
    assert "depends on suppliers." in cleaned

import json

from src.ingestion.sec.preprocessing import ProcessedFilingExporter


def test_processed_filing_exporter():
    metadata = FilingMetadata(
        cik="0001045810",
        accession_number="0001045810-26-000001",
        company_name="NVIDIA Corporation",
        filing_date="2026-02-25",
        form="10-K",
        source_url="https://www.sec.gov/example",
    )

    section = ParsedSection(
        item="1A",
        title="Risk Factors",
        text="NVIDIA depends on semiconductor suppliers.",
        paragraphs=(),
    )

    parsed_filing = ParsedFiling(
        metadata=metadata,
        sections=(section,),
    )

    processor = FilingPreprocessor()
    processed_filing = processor.process(parsed_filing)

    exporter = ProcessedFilingExporter()

    from pathlib import Path

    output_file = Path("data/test/processed_filing.json")

    saved_path = exporter.save_json(
        processed_filing,
        output_file,
    )

    assert saved_path.exists()

    with saved_path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    assert data["company_name"] == "NVIDIA Corporation"
    assert data["sections"][0]["item_number"] == "1A"
    assert len(data["sections"][0]["chunks"]) >= 1

    saved_path.unlink(missing_ok=True)