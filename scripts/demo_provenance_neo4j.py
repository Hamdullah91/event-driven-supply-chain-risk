import os

from dotenv import load_dotenv
from neo4j import GraphDatabase

from src.graph.provenance.models import (
    ExtractedRelationship,
    ProvenanceMetadata,
)
from src.graph.provenance.repository import (
    ProvenanceRelationshipRepository,
)


load_dotenv()


def main() -> None:
    uri = os.environ["NEO4J_URI"]
    username = os.environ["NEO4J_USERNAME"]
    password = os.environ["NEO4J_PASSWORD"]

    driver = GraphDatabase.driver(
        uri,
        auth=(username, password),
    )

    try:
        driver.verify_connectivity()

        repository = ProvenanceRelationshipRepository(driver)

        relationship = ExtractedRelationship(
            source_entity="NVIDIA",
            relationship_type="DEPENDS_ON",
            target_entity="TSMC",
            provenance=ProvenanceMetadata(
                source="SEC_EDGAR",
                source_document="0001045810-25-000023",
                filing_date="2025-02-26",
                extraction_method="spacy_triplet",
                confidence=0.91,
            ),
        )

        repository.upsert_relationship(relationship)

        print("Provenance relationship stored successfully.")

    finally:
        driver.close()


if __name__ == "__main__":
    main()