from __future__ import annotations

from typing import Any

from src.graph.connection import Neo4jConnection
from src.graph.contracts import CANONICAL_ID_PROPERTIES


class GraphContractAudit:
    """Read-only checks for frontend-critical graph data contracts."""

    def __init__(self, connection: Neo4jConnection) -> None:
        self.connection = connection

    def canonical_id_completeness(self) -> dict[str, Any]:
        rows: list[dict[str, Any]] = []
        with self.connection.driver.session() as session:
            for label, identity_property in CANONICAL_ID_PROPERTIES.items():
                query = f"""
                MATCH (n:{label})
                RETURN count(n) AS total,
                       count(CASE WHEN n.{identity_property} IS NULL
                                      OR trim(toString(n.{identity_property})) = ''
                                  THEN 1 END) AS missing
                """
                record = session.run(query).single()
                total = int(record["total"]) if record else 0
                missing = int(record["missing"]) if record else 0
                rows.append(
                    {
                        "label": label,
                        "identity_property": identity_property,
                        "total": total,
                        "missing": missing,
                        "complete": missing == 0,
                    }
                )
        return {
            "complete": all(row["complete"] for row in rows),
            "labels": rows,
        }

    def geographic_coordinate_completeness(self) -> dict[str, Any]:
        query = """
        MATCH (l:Location)
        RETURN count(l) AS total,
               count(CASE WHEN l.latitude IS NOT NULL AND l.longitude IS NOT NULL THEN 1 END) AS geocoded,
               count(CASE WHEN (l.latitude IS NULL) <> (l.longitude IS NULL) THEN 1 END) AS partial
        """
        with self.connection.driver.session() as session:
            record = session.run(query).single()
        total = int(record["total"]) if record else 0
        geocoded = int(record["geocoded"]) if record else 0
        partial = int(record["partial"]) if record else 0
        return {
            "total": total,
            "geocoded": geocoded,
            "missing": max(total - geocoded - partial, 0),
            "partial": partial,
            "contract_valid": partial == 0,
        }

    def provenance_completeness(self) -> dict[str, Any]:
        relationship_query = """
        MATCH ()-[r]->()
        WITH type(r) AS relationship_type, r
        RETURN relationship_type,
               count(r) AS total,
               count(CASE WHEN r.source_type IS NOT NULL OR r.source IS NOT NULL THEN 1 END) AS with_source,
               count(CASE WHEN r.source_url IS NOT NULL THEN 1 END) AS with_source_url,
               count(CASE WHEN r.confidence IS NOT NULL THEN 1 END) AS with_confidence,
               count(CASE WHEN r.verification_status IS NOT NULL THEN 1 END) AS with_verification_status,
               count(CASE WHEN r.derivation IS NOT NULL THEN 1 END) AS with_derivation,
               count(CASE WHEN r.link_method IS NOT NULL THEN 1 END) AS with_link_method,
               count(CASE WHEN r.linked_at IS NOT NULL THEN 1 END) AS with_linked_at
        ORDER BY relationship_type
        """
        event_query = """
        MATCH (e:Event)
        RETURN count(e) AS total,
               count(CASE WHEN e.source IS NOT NULL AND trim(toString(e.source)) <> '' THEN 1 END) AS with_source,
               count(CASE WHEN e.timestamp IS NOT NULL THEN 1 END) AS with_timestamp,
               count(CASE WHEN e.confidence IS NOT NULL THEN 1 END) AS with_confidence,
               count(CASE WHEN e.description IS NOT NULL AND trim(toString(e.description)) <> '' THEN 1 END) AS with_description
        """
        with self.connection.driver.session() as session:
            relationship_records = list(session.run(relationship_query))
            event_record = session.run(event_query).single()

        relationships: list[dict[str, Any]] = []
        relationship_total = 0
        for record in relationship_records:
            row = {
                key: int(record[key]) if key != "relationship_type" else str(record[key])
                for key in record.keys()
            }
            relationship_total += row["total"]
            relationships.append(row)

        event_total = int(event_record["total"]) if event_record else 0
        events: dict[str, Any] = {
            "total": event_total,
            "with_source": int(event_record["with_source"]) if event_record else 0,
            "with_timestamp": int(event_record["with_timestamp"]) if event_record else 0,
            "with_confidence": int(event_record["with_confidence"]) if event_record else 0,
            "with_description": int(event_record["with_description"]) if event_record else 0,
        }
        core_fields = ("with_source", "with_timestamp", "with_confidence")
        events["core_evidence_fields"] = list(core_fields)
        events["core_evidence_complete"] = event_total == 0 or all(
            events[field] == event_total for field in core_fields
        )
        events["description_complete"] = (
            event_total == 0 or events["with_description"] == event_total
        )

        return {
            "relationship_total": relationship_total,
            "relationships": relationships,
            "events": events,
            "note": (
                "Relationship provenance is reported by field/type because seeded, "
                "extracted, derived, and dynamic links have different evidence contracts. "
                "Event core_evidence_complete explicitly means source + timestamp + "
                "confidence; description completeness is reported separately."
            ),
        }
