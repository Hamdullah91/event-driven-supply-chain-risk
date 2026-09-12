from __future__ import annotations

from src.graph.connection import Neo4jConnection
from src.risk.models import (
    DirectAffectedCompany,
    SupplyEdge,
    TwoHopSupplyPath,
)


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

    def get_two_hop_downstream(
        self,
        company_id: str,
    ) -> list[TwoHopSupplyPath]:
        """Traverse exactly two canonical supplier -> customer edges."""

        query = """
        MATCH (source:Company {company_id: $company_id})-[r1:SUPPLIES]->(hop1:Company)
              -[r2:SUPPLIES]->(hop2:Company)
        WHERE source <> hop1
          AND source <> hop2
          AND hop1 <> hop2
        RETURN DISTINCT
            source.company_id AS source_company_id,
            source.name AS source_company_name,
            hop1.company_id AS hop_1_company_id,
            hop1.name AS hop_1_company_name,
            hop2.company_id AS hop_2_company_id,
            hop2.name AS hop_2_company_name,
            coalesce(r1.dependency_weight, $default_weight) AS hop_1_weight,
            CASE
                WHEN r1.dependency_weight IS NULL THEN 'default'
                ELSE 'relationship'
            END AS hop_1_weight_source,
            coalesce(r2.dependency_weight, $default_weight) AS hop_2_weight,
            CASE
                WHEN r2.dependency_weight IS NULL THEN 'default'
                ELSE 'relationship'
            END AS hop_2_weight_source
        ORDER BY hop_1_company_id, hop_2_company_id
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
            TwoHopSupplyPath(
                source_company_id=str(record["source_company_id"]),
                source_company_name=str(record["source_company_name"]),
                hop_1_company_id=str(record["hop_1_company_id"]),
                hop_1_company_name=str(record["hop_1_company_name"]),
                hop_2_company_id=str(record["hop_2_company_id"]),
                hop_2_company_name=str(record["hop_2_company_name"]),
                hop_1_weight=float(record["hop_1_weight"]),
                hop_1_weight_source=str(record["hop_1_weight_source"]),
                hop_2_weight=float(record["hop_2_weight"]),
                hop_2_weight_source=str(record["hop_2_weight_source"]),
            )
            for record in records
        ]
