from __future__ import annotations

from src.graph.connection import Neo4jConnection
from src.risk.models import DirectAffectedCompany, SupplyEdge


DEFAULT_DEPENDENCY_WEIGHT = 1.0


class RiskRepository:
    """Read-only graph access required by the risk propagation engine."""

    def __init__(self, connection: Neo4jConnection) -> None:
        self.connection = connection

    def get_directly_affected_companies(
        self,
        event_id: str,
    ) -> list[DirectAffectedCompany]:
        query = """
        MATCH (event:Event {event_id: $event_id})-[:AFFECTS]->(company:Company)
        RETURN
            event.event_id AS event_id,
            company.company_id AS company_id,
            company.name AS company_name,
            event.severity AS severity
        ORDER BY company.company_id
        """

        with self.connection.driver.session() as session:
            records = list(session.run(query, event_id=event_id))

        return [
            DirectAffectedCompany(
                event_id=str(record["event_id"]),
                company_id=str(record["company_id"]),
                company_name=str(record["company_name"]),
                severity=str(record["severity"]),
            )
            for record in records
        ]

    def get_one_hop_downstream(
        self,
        company_id: str,
    ) -> list[SupplyEdge]:
        """Traverse exactly one canonical supplier -> customer edge."""

        query = """
        MATCH (source:Company {company_id: $company_id})-[r:SUPPLIES]->(target:Company)
        RETURN
            source.company_id AS source_company_id,
            source.name AS source_company_name,
            target.company_id AS target_company_id,
            target.name AS target_company_name,
            coalesce(r.dependency_weight, $default_weight) AS dependency_weight,
            CASE
                WHEN r.dependency_weight IS NULL THEN 'default'
                ELSE 'relationship'
            END AS weight_source
        ORDER BY target.company_id
        """

        with self.connection.driver.session() as session:
            records = list(
                session.run(
                    query,
                    company_id=company_id,
                    default_weight=DEFAULT_DEPENDENCY_WEIGHT,
                )
            )

        return [
            SupplyEdge(
                source_company_id=str(record["source_company_id"]),
                source_company_name=str(record["source_company_name"]),
                target_company_id=str(record["target_company_id"]),
                target_company_name=str(record["target_company_name"]),
                dependency_weight=float(record["dependency_weight"]),
                weight_source=str(record["weight_source"]),
            )
            for record in records
        ]
