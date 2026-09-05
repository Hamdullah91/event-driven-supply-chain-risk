from __future__ import annotations

from src.graph.connection import Neo4jConnection
from src.graph.ingestion.models import GraphIngestionRelationship


ALLOWED_NODE_TYPES = {
    "Company",
    "Facility",
    "Product",
    "Material",
    "Location",
    "Country",
    "Technology",
    "Industry",
}

ALLOWED_RELATIONSHIPS = {
    "SUPPLIES",
    "DEPENDS_ON",
    "OPERATES",
    "OWNS",
    "USES",
    "PRODUCES",
    "LOCATED_IN",
    "OPERATES_IN",
}


class GraphIngestionRepository:
    def __init__(self, connection: Neo4jConnection) -> None:
        self.connection = connection

    def save_relationship(
        self,
        relationship: GraphIngestionRelationship,
    ) -> None:

        subject_type = relationship.subject_type
        object_type = relationship.object_type
        relationship_type = relationship.relationship.upper()

        if subject_type not in ALLOWED_NODE_TYPES:
            raise ValueError(
                f"Unsupported subject node type: {subject_type}"
            )

        if object_type not in ALLOWED_NODE_TYPES:
            raise ValueError(
                f"Unsupported object node type: {object_type}"
            )

        if relationship_type not in ALLOWED_RELATIONSHIPS:
            raise ValueError(
                f"Unsupported relationship type: {relationship_type}"
            )

        query = f"""
        MERGE (subject:{subject_type} {{name: $subject}})
        MERGE (object:{object_type} {{name: $object}})

        MERGE (subject)-[r:{relationship_type}]->(object)

        SET
            r.source = $source,
            r.source_document = $source_document,
            r.source_url = $source_url,
            r.filing_date = $filing_date,
            r.extraction_method = $extraction_method,
            r.confidence = $confidence,
            r.created_at = $created_at
        """

        provenance = relationship.provenance

        with self.connection.driver.session() as session:
            session.run(
                query,
                subject=relationship.subject,
                object=relationship.object,
                source=provenance.source,
                source_document=provenance.source_document,
                source_url=provenance.source_url,
                filing_date=(
                    provenance.filing_date.isoformat()
                    if provenance.filing_date
                    else None
                ),
                extraction_method=provenance.extraction_method,
                confidence=provenance.confidence,
                created_at=provenance.created_at.isoformat(),
            ).consume()