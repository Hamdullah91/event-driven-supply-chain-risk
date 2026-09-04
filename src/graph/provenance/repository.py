from __future__ import annotations

from neo4j import Driver

from src.graph.provenance.models import ExtractedRelationship
from src.graph.provenance.service import provenance_to_neo4j


RELATIONSHIP_SCHEMA: dict[str, tuple[str, tuple[str, ...]]] = {
    "SUPPLIES": ("Company", ("Company",)),
    "DEPENDS_ON": ("Company", ("Company",)),
    "OPERATES": ("Company", ("Facility",)),
    "OWNS": ("Company", ("Facility",)),
    "USES": ("Company", ("Material", "Technology")),
    "PRODUCES": ("Company", ("Product", "Material")),
    "LOCATED_IN": ("Facility", ("Location",)),
    "OPERATES_IN": ("Company", ("Industry",)),
}


class ProvenanceRelationshipRepository:
    def __init__(self, driver: Driver) -> None:
        self.driver = driver

    def upsert_relationship(
        self,
        relationship: ExtractedRelationship,
    ) -> None:
        relationship_type = relationship.relationship_type.upper()

        schema = RELATIONSHIP_SCHEMA.get(relationship_type)

        if schema is None:
            raise ValueError(
                f"Unsupported relationship type: {relationship_type}"
            )

        source_label, target_labels = schema

        target_match = " OR ".join(
            f"target:{label}"
            for label in target_labels
        )

        query = f"""
        MATCH (source:{source_label} {{name: $source_name}})
        MATCH (target {{name: $target_name}})
        WHERE {target_match}

        MERGE (source)-[r:{relationship_type}]->(target)

        SET r.source = $source,
            r.source_document = $source_document,
            r.source_url = $source_url,
            r.filing_date =
                CASE
                    WHEN $filing_date IS NULL
                    THEN NULL
                    ELSE date($filing_date)
                END,
            r.extraction_method = $extraction_method,
            r.confidence =
                CASE
                    WHEN r.confidence IS NULL
                        OR $confidence > r.confidence
                    THEN $confidence
                    ELSE r.confidence
                END,
            r.created_at = datetime($created_at)

        RETURN r
        """

        provenance = provenance_to_neo4j(
            relationship.provenance
        )

        parameters = {
            "source_name": relationship.source_entity,
            "target_name": relationship.target_entity,
            **provenance,
        }

        with self.driver.session() as session:
            session.run(
                query,
                parameters,
            ).consume()