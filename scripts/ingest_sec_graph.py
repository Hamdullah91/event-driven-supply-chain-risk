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


PROCESSED_FILING_PATH = Path(
    "data/processed/sec/"
    "1045810/"
    "0001045810-26-000021/"
    "processed.json"
)


def load_processed_filing(path: Path) -> dict:
    if not path.exists():
        raise FileNotFoundError(
            f"Processed SEC filing not found: {path}"
        )

    with path.open(
        "r",
        encoding="utf-8",
    ) as file:
        return json.load(file)


def main() -> None:
    filing = load_processed_filing(
        PROCESSED_FILING_PATH
    )

    logger.info(
        "Loading processed SEC filing: %s",
        filing["accession_number"],
    )

    # Load spaCy model
    nlp = spacy.load("en_core_web_sm")

    # NLP triplet extraction
    triplet_extractor = TripletExtractor(nlp)

    # Neo4j connection
    connection = Neo4jConnection()

    try:
        connection.verify_connection()

        logger.info(
            "Neo4j connection verified."
        )

        repository = GraphIngestionRepository(
            connection
        )

        pipeline = GraphIngestionPipeline(
            repository
        )

        service = SECGraphIngestionService(
            triplet_extractor=triplet_extractor,
            graph_pipeline=pipeline,
        )

        total_attempted = 0
        total_inserted = 0
        total_rejected = 0

        filing_date = date.fromisoformat(
            filing["filing_date"]
        )

        for section in filing["sections"]:

            logger.info(
                "Processing section: %s",
                section["item_number"],
            )

            for chunk in section["chunks"]:

                text = chunk["text"]

                result = service.ingest_text(
                    text,
                    filing_company=filing["company_name"],
                    source_document=filing[
                        "accession_number"
                    ],
                    source_url=filing[
                        "source_url"
                    ],
                    filing_date=filing_date,
                )

                total_attempted += result[
                    "attempted"
                ]

                total_inserted += result[
                    "inserted"
                ]

                total_rejected += result[
                    "rejected"
                ]

        print()
        print("===== DAY 24 GRAPH INGESTION =====")
        print(
            f"Company: {filing['company_name']}"
        )
        print(
            f"Accession: {filing['accession_number']}"
        )
        print(
            f"Attempted: {total_attempted}"
        )
        print(
            f"Inserted: {total_inserted}"
        )
        print(
            f"Rejected: {total_rejected}"
        )
        print("==================================")

    finally:
        connection.close()


if __name__ == "__main__":
    main()