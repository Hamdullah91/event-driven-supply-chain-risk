from __future__ import annotations

from src.graph.connection import Neo4jConnection
from src.graph.ingestion.models import GraphIngestionRelationship
from src.nlp.entity_resolution.resolver import resolve_company


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

    @staticmethod
    def _resolve_company_id(name: str) -> str:
        resolved = resolve_company(name)

        if resolved.canonical_id is None:
            raise ValueError(
                f"Cannot persist unresolved Company entity: {name}"
            )

        return resolved.canonical_id

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

        if subject_type == "Company" and object_type == "Company":
            subject_id = self._resolve_company_id(
                relationship.subject
            )
            object_id = self._resolve_company_id(
                relationship.object
            )

            query = f"""
            MERGE (subject:Company {{company_id: $subject_id}})
            ON CREATE SET subject.name = $subject_name

            MERGE (object:Company {{company_id: $object_id}})
            ON CREATE SET object.name = $object_name

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

            subject_params = {
                "subject_id": subject_id,
                "subject_name": relationship.subject,
                "object_id": object_id,
                "object_name": relationship.object,
            }
        else:
            query = f"""
            MERGE (subject:{subject_type} {{name: $subject_name}})
            MERGE (object:{object_type} {{name: $object_name}})

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

            subject_params = {
                "subject_name": relationship.subject,
                "object_name": relationship.object,
            }

        provenance = relationship.provenance

        with self.connection.driver.session() as session:
            session.run(
                query,
                **subject_params,
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
