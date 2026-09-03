from __future__ import annotations

import json
from pathlib import Path

from src.ingestion.sec.parser.filing_parser import SEC10KParser
from src.ingestion.sec.parser.models import FilingMetadata
from src.ingestion.sec.preprocessing import (
    FilingPreprocessor,
    ProcessedFilingExporter,
)


def main() -> None:
    filing_dir = Path(
        "data/raw/sec/1045810/0001045810-26-000021"
    )

    html_path = filing_dir / "10-k.htm"
    metadata_path = filing_dir / "metadata.json"

    html = html_path.read_text(
        encoding="utf-8",
        errors="ignore",
    )

    with metadata_path.open(
        "r",
        encoding="utf-8",
    ) as file:
        metadata_data = json.load(file)

    metadata = FilingMetadata(
        cik=metadata_data["cik"],
        accession_number=metadata_data["accession_number"],
        company_name=metadata_data["company_name"],
        filing_date=metadata_data["filing_date"],
        form=metadata_data["form"],
        source_url=metadata_data["source_url"],
    )

    parser = SEC10KParser()

    parsed_filing = parser.parse(
        html=html,
        metadata=metadata,
    )

    preprocessor = FilingPreprocessor()

    processed_filing = preprocessor.process(
        parsed_filing
    )

    exporter = ProcessedFilingExporter()

    output_path = Path(
        "data/processed/sec/"
        "1045810/"
        "0001045810-26-000021/"
        "processed.json"
    )

    exporter.save_json(
        processed_filing,
        output_path,
    )

    print(
        f"Processed filing saved to: {output_path}"
    )

    print(
        f"Sections: {len(processed_filing.sections)}"
    )

    total_chunks = sum(
        len(section.chunks)
        for section in processed_filing.sections
    )

    print(
        f"Chunks: {total_chunks}"
    )


if __name__ == "__main__":
    main()