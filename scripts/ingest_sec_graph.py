from __future__ import annotations

import json
import logging
from datetime import date
from pathlib import Path

import spacy

from src.graph.connection import Neo4jConnection
from src.graph.ingestion.pipeline import GraphIngestionPipeline
from src.graph.ingestion.repository import GraphIngestionRepository
from src.graph.ingestion.service import SECGraphIngestionService
from src.nlp.triplet_extractor import TripletExtractor


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)

logger = logging.getLogger(__name__)

PROCESSED_SEC_ROOT = Path("data/processed/sec")


def discover_processed_filings(
    root: Path = PROCESSED_SEC_ROOT,
) -> list[Path]:
    """Return every processed SEC filing available for graph ingestion."""
    if not root.exists():
        return []

    return sorted(root.rglob("processed.json"))


def load_processed_filing(path: Path) -> dict:
    if not path.exists():
        raise FileNotFoundError(
            f"Processed SEC filing not found: {path}"
        )

    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def ingest_filing(
    filing: dict,
    *,
    service: SECGraphIngestionService,
) -> dict[str, int]:
    logger.info(
        "Loading processed SEC filing company=%s accession=%s",
        filing["company_name"],
        filing["accession_number"],
    )

    total_attempted = 0
    total_inserted = 0
    total_rejected = 0

    filing_date = date.fromisoformat(
        filing["filing_date"]
    )

    for section in filing.get("sections", []):
        logger.info(
            "Processing section: %s",
            section.get("item_number"),
        )

        for chunk in section.get("chunks", []):
            text = chunk.get("text", "").strip()
            if not text:
                continue

            result = service.ingest_text(
                text,
                filing_company=filing["company_name"],
                source_document=filing["accession_number"],
                source_url=filing.get("source_url"),
                filing_date=filing_date,
            )

            total_attempted += result["attempted"]
            total_inserted += result["inserted"]
            total_rejected += result["rejected"]

    return {
        "attempted": total_attempted,
        "inserted": total_inserted,
        "rejected": total_rejected,
    }


def main() -> None:
    processed_paths = discover_processed_filings()

    if not processed_paths:
        raise FileNotFoundError(
            f"No processed SEC filings found under {PROCESSED_SEC_ROOT}"
        )

    nlp = spacy.load("en_core_web_sm")
    triplet_extractor = TripletExtractor(nlp)

    connection = Neo4jConnection()

    try:
        connection.verify_connection()
        logger.info("Neo4j connection verified.")

        repository = GraphIngestionRepository(connection)
        pipeline = GraphIngestionPipeline(repository)
        service = SECGraphIngestionService(
            triplet_extractor=triplet_extractor,
            graph_pipeline=pipeline,
        )

        total_attempted = 0
        total_inserted = 0
        total_rejected = 0
        succeeded = 0
        failed = 0

        for processed_path in processed_paths:
            try:
                filing = load_processed_filing(
                    processed_path
                )
                result = ingest_filing(
                    filing,
                    service=service,
                )

                succeeded += 1
                total_attempted += result["attempted"]
                total_inserted += result["inserted"]
                total_rejected += result["rejected"]

                logger.info(
                    "SEC graph ingestion complete company=%s accession=%s attempted=%d inserted=%d rejected=%d",
                    filing["company_name"],
                    filing["accession_number"],
                    result["attempted"],
                    result["inserted"],
                    result["rejected"],
                )
            except Exception:
                failed += 1
                logger.exception(
                    "Failed SEC graph ingestion for: %s",
                    processed_path,
                )

        print()
        print("===== SEC BATCH GRAPH INGESTION =====")
        print(f"Discovered filings: {len(processed_paths)}")
        print(f"Succeeded filings: {succeeded}")
        print(f"Failed filings: {failed}")
        print(f"Attempted relationships: {total_attempted}")
        print(f"Inserted relationships: {total_inserted}")
        print(f"Rejected relationships: {total_rejected}")
        print("=====================================")

        if failed:
            raise SystemExit(1)

    finally:
        connection.close()


if __name__ == "__main__":
    main()
