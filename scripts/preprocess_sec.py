from __future__ import annotations

import json
import logging
from pathlib import Path

from src.ingestion.sec.parser.filing_parser import SEC10KParser
from src.ingestion.sec.parser.models import FilingMetadata
from src.ingestion.sec.preprocessing import (
    FilingPreprocessor,
    ProcessedFilingExporter,
)


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)

logger = logging.getLogger(__name__)

RAW_SEC_ROOT = Path("data/raw/sec")
PROCESSED_SEC_ROOT = Path("data/processed/sec")


def discover_filing_dirs(root: Path = RAW_SEC_ROOT) -> list[Path]:
    """Return SEC filing directories that contain both HTML and metadata."""
    filing_dirs: list[Path] = []

    if not root.exists():
        return filing_dirs

    for metadata_path in root.rglob("metadata.json"):
        filing_dir = metadata_path.parent
        if (filing_dir / "10-k.htm").exists():
            filing_dirs.append(filing_dir)

    return sorted(filing_dirs)


def load_metadata(path: Path) -> FilingMetadata:
    with path.open("r", encoding="utf-8") as file:
        metadata_data = json.load(file)

    return FilingMetadata(
        cik=metadata_data["cik"],
        accession_number=metadata_data["accession_number"],
        company_name=metadata_data["company_name"],
        filing_date=metadata_data["filing_date"],
        form=metadata_data["form"],
        source_url=metadata_data["source_url"],
    )


def process_filing(
    filing_dir: Path,
    *,
    parser: SEC10KParser,
    preprocessor: FilingPreprocessor,
    exporter: ProcessedFilingExporter,
) -> Path:
    html_path = filing_dir / "10-k.htm"
    metadata_path = filing_dir / "metadata.json"

    html = html_path.read_text(
        encoding="utf-8",
        errors="ignore",
    )
    metadata = load_metadata(metadata_path)

    parsed_filing = parser.parse(
        html=html,
        metadata=metadata,
    )
    processed_filing = preprocessor.process(parsed_filing)

    output_path = (
        PROCESSED_SEC_ROOT
        / str(metadata.cik)
        / metadata.accession_number
        / "processed.json"
    )

    exporter.save_json(
        processed_filing,
        output_path,
    )

    total_chunks = sum(
        len(section.chunks)
        for section in processed_filing.sections
    )

    logger.info(
        "Processed SEC filing company=%s accession=%s sections=%d chunks=%d output=%s",
        metadata.company_name,
        metadata.accession_number,
        len(processed_filing.sections),
        total_chunks,
        output_path,
    )

    return output_path


def main() -> None:
    filing_dirs = discover_filing_dirs()

    if not filing_dirs:
        raise FileNotFoundError(
            f"No SEC filing directories found under {RAW_SEC_ROOT}"
        )

    parser = SEC10KParser()
    preprocessor = FilingPreprocessor()
    exporter = ProcessedFilingExporter()

    succeeded = 0
    failed = 0

    for filing_dir in filing_dirs:
        try:
            process_filing(
                filing_dir,
                parser=parser,
                preprocessor=preprocessor,
                exporter=exporter,
            )
            succeeded += 1
        except Exception:
            failed += 1
            logger.exception(
                "Failed to preprocess SEC filing: %s",
                filing_dir,
            )

    print()
    print("===== SEC BATCH PREPROCESSING =====")
    print(f"Discovered: {len(filing_dirs)}")
    print(f"Succeeded: {succeeded}")
    print(f"Failed: {failed}")
    print("===================================")

    if failed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
