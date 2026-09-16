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
                rows.append({"label": label, "identity_property": identity_property, "total": total, "missing": missing, "complete": missing == 0})
        return {"complete": all(row["complete"] for row in rows), "labels": rows}

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
        return {"total": total, "geocoded": geocoded, "missing": max(total - geocoded - partial, 0), "partial": partial, "contract_valid": partial == 0}
