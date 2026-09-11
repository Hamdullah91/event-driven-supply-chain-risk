from __future__ import annotations

from src.graph.connection import Neo4jConnection
from src.graph.ingestion.models import GraphIngestionRelationship
from src.nlp.entity_resolution.organizational_identity import (
    resolve_organizational_identity,
)
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
    def _resolve_company_identity(name: str) -> tuple[str, str]:
        resolved = resolve_company(name)

        if resolved.canonical_id is not None:
            return resolved.canonical_id, "CANONICAL"

        identity = resolve_organizational_identity(name)
        if (
            identity is not None
            and identity.identity_type == "VERIFIED_EXTERNAL"
        ):
            external_id = (
                "external:"
                + "_".join(
                    identity.normalized_name.lower().split()
                )
            )
            return external_id, "VERIFIED_EXTERNAL"

        raise ValueError(
            f"Cannot persist unresolved Company entity: {name}"
        )

    @classmethod
    def _node_merge(
        cls,
        *,
        role: str,
        node_type: str,
        name: str,
    ) -> tuple[str, dict[str, str]]:
        if node_type == "Company":
            company_id, identity_state = cls._resolve_company_identity(name)
            clause = f"""
            MERGE ({role}:Company {{company_id: ${role}_id}})
            ON CREATE SET {role}.name = ${role}_name
            SET {role}.identity_state = ${role}_identity_state
            """
            params = {
                f"{role}_id": company_id,
                f"{role}_name": name,
                f"{role}_identity_state": identity_state,
            }
            return clause, params

        clause = f"MERGE ({role}:{node_type} {{name: ${role}_name}})"
        return clause, {f"{role}_name": name}

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

        subject_merge, subject_params = self._node_merge(
            role="subject",
            node_type=subject_type,
            name=relationship.subject,
        )
        object_merge, object_params = self._node_merge(
            role="object",
            node_type=object_type,
            name=relationship.object,
        )

        query = f"""
        {subject_merge}
        {object_merge}

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
        params = {**subject_params, **object_params}

        with self.connection.driver.session() as session:
            session.run(
                query,
                **params,
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
