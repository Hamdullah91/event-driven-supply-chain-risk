from __future__ import annotations

from src.graph.connection import Neo4jConnection
from src.risk.models import (
    DirectAffectedCompany,
    SupplyEdge,
    ThreeHopSupplyPath,
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

    def get_one_hop_downstream(self, company_id: str) -> list[SupplyEdge]:
        query = """
        MATCH (source:Company {company_id: $company_id})-[r:SUPPLIES]->(target:Company)
        RETURN source.company_id AS source_company_id, source.name AS source_company_name,
               target.company_id AS target_company_id, target.name AS target_company_name,
               coalesce(r.dependency_weight, $default_weight) AS dependency_weight,
               CASE WHEN r.dependency_weight IS NULL THEN 'default' ELSE 'relationship' END AS weight_source
        ORDER BY target.company_id
        """
        with self.connection.driver.session() as session:
            records = list(session.run(query, company_id=company_id, default_weight=DEFAULT_DEPENDENCY_WEIGHT))
        return [SupplyEdge(source_company_id=str(r["source_company_id"]), source_company_name=str(r["source_company_name"]), target_company_id=str(r["target_company_id"]), target_company_name=str(r["target_company_name"]), dependency_weight=float(r["dependency_weight"]), weight_source=str(r["weight_source"])) for r in records]

    def get_two_hop_downstream(self, company_id: str) -> list[TwoHopSupplyPath]:
        query = """
        MATCH (source:Company {company_id: $company_id})-[r1:SUPPLIES]->(hop1:Company)-[r2:SUPPLIES]->(hop2:Company)
        WHERE source <> hop1 AND source <> hop2 AND hop1 <> hop2
        RETURN DISTINCT source.company_id AS source_company_id, source.name AS source_company_name,
            hop1.company_id AS hop_1_company_id, hop1.name AS hop_1_company_name,
            hop2.company_id AS hop_2_company_id, hop2.name AS hop_2_company_name,
            coalesce(r1.dependency_weight, $default_weight) AS hop_1_weight,
            CASE WHEN r1.dependency_weight IS NULL THEN 'default' ELSE 'relationship' END AS hop_1_weight_source,
            coalesce(r2.dependency_weight, $default_weight) AS hop_2_weight,
            CASE WHEN r2.dependency_weight IS NULL THEN 'default' ELSE 'relationship' END AS hop_2_weight_source
        ORDER BY hop_1_company_id, hop_2_company_id
        """
        with self.connection.driver.session() as session:
            records = list(session.run(query, company_id=company_id, default_weight=DEFAULT_DEPENDENCY_WEIGHT))
        return [TwoHopSupplyPath(source_company_id=str(r["source_company_id"]), source_company_name=str(r["source_company_name"]), hop_1_company_id=str(r["hop_1_company_id"]), hop_1_company_name=str(r["hop_1_company_name"]), hop_2_company_id=str(r["hop_2_company_id"]), hop_2_company_name=str(r["hop_2_company_name"]), hop_1_weight=float(r["hop_1_weight"]), hop_1_weight_source=str(r["hop_1_weight_source"]), hop_2_weight=float(r["hop_2_weight"]), hop_2_weight_source=str(r["hop_2_weight_source"])) for r in records]

    def get_three_hop_downstream(self, company_id: str) -> list[ThreeHopSupplyPath]:
        query = """
        MATCH (source:Company {company_id: $company_id})-[r1:SUPPLIES]->(hop1:Company)-[r2:SUPPLIES]->(hop2:Company)-[r3:SUPPLIES]->(hop3:Company)
        WHERE source <> hop1 AND source <> hop2 AND source <> hop3 AND hop1 <> hop2 AND hop1 <> hop3 AND hop2 <> hop3
        RETURN DISTINCT source.company_id AS source_company_id, source.name AS source_company_name,
            hop1.company_id AS hop_1_company_id, hop1.name AS hop_1_company_name,
            hop2.company_id AS hop_2_company_id, hop2.name AS hop_2_company_name,
            hop3.company_id AS hop_3_company_id, hop3.name AS hop_3_company_name,
            coalesce(r1.dependency_weight, $default_weight) AS hop_1_weight,
            CASE WHEN r1.dependency_weight IS NULL THEN 'default' ELSE 'relationship' END AS hop_1_weight_source,
            coalesce(r2.dependency_weight, $default_weight) AS hop_2_weight,
            CASE WHEN r2.dependency_weight IS NULL THEN 'default' ELSE 'relationship' END AS hop_2_weight_source,
            coalesce(r3.dependency_weight, $default_weight) AS hop_3_weight,
            CASE WHEN r3.dependency_weight IS NULL THEN 'default' ELSE 'relationship' END AS hop_3_weight_source
        ORDER BY hop_1_company_id, hop_2_company_id, hop_3_company_id
        """
        with self.connection.driver.session() as session:
            records = list(session.run(query, company_id=company_id, default_weight=DEFAULT_DEPENDENCY_WEIGHT))
        return [ThreeHopSupplyPath(source_company_id=str(r["source_company_id"]), source_company_name=str(r["source_company_name"]), hop_1_company_id=str(r["hop_1_company_id"]), hop_1_company_name=str(r["hop_1_company_name"]), hop_2_company_id=str(r["hop_2_company_id"]), hop_2_company_name=str(r["hop_2_company_name"]), hop_3_company_id=str(r["hop_3_company_id"]), hop_3_company_name=str(r["hop_3_company_name"]), hop_1_weight=float(r["hop_1_weight"]), hop_1_weight_source=str(r["hop_1_weight_source"]), hop_2_weight=float(r["hop_2_weight"]), hop_2_weight_source=str(r["hop_2_weight_source"]), hop_3_weight=float(r["hop_3_weight"]), hop_3_weight_source=str(r["hop_3_weight_source"])) for r in records]

    def company_exists(self, company_id: str) -> bool:
        query = "MATCH (company:Company {company_id: $company_id}) RETURN count(company) > 0 AS exists"
        with self.connection.driver.session() as session:
            record = session.run(query, company_id=company_id).single()
        return bool(record["exists"]) if record else False

    def event_exists(self, event_id: str) -> bool:
        query = "MATCH (event:Event {event_id: $event_id}) RETURN count(event) > 0 AS exists"
        with self.connection.driver.session() as session:
            record = session.run(query, event_id=event_id).single()
        return bool(record["exists"]) if record else False

    def get_company_blast_radius(self, company_id: str, *, max_hops: int = 3) -> list[dict]:
        if max_hops not in {1, 2, 3}:
            raise ValueError("max_hops must be between 1 and 3.")
        query = f"""
        MATCH path = (source:Company {{company_id: $company_id}})-[:SUPPLIES*1..{max_hops}]->(target:Company)
        WHERE target <> source AND all(node IN nodes(path) WHERE single(other IN nodes(path) WHERE other = node))
        WITH source, target, path, length(path) AS hop_distance
        RETURN source.company_id AS source_company_id, source.name AS source_company_name,
            target.company_id AS target_company_id, target.name AS target_company_name, hop_distance,
            [node IN nodes(path) | {{company_id: node.company_id, name: node.name}}] AS path_nodes,
            [relationship IN relationships(path) | {{dependency_weight: coalesce(relationship.dependency_weight, $default_weight), weight_source: CASE WHEN relationship.dependency_weight IS NULL THEN 'default' ELSE 'relationship' END}}] AS path_relationships
        ORDER BY hop_distance, target.company_id
        """
        with self.connection.driver.session() as session:
            records = list(session.run(query, company_id=company_id, default_weight=DEFAULT_DEPENDENCY_WEIGHT))
        return [dict(record) for record in records]

    def get_event_blast_radius(self, event_id: str, *, max_hops: int = 3) -> list[dict]:
        """Return direct and downstream company paths originating from one Event."""
        if max_hops not in {1, 2, 3}:
            raise ValueError("max_hops must be between 1 and 3.")
        query = f"""
        MATCH (event:Event {{event_id: $event_id}})-[:AFFECTS]->(source:Company)
        MATCH path = (source)-[:SUPPLIES*0..{max_hops}]->(target:Company)
        WHERE all(node IN nodes(path) WHERE single(other IN nodes(path) WHERE other = node))
        WITH event, source, target, path, length(path) AS hop_distance
        RETURN DISTINCT
            event.event_id AS event_id,
            event.event_type AS event_type,
            event.severity AS severity,
            source.company_id AS affected_company_id,
            source.name AS affected_company_name,
            target.company_id AS target_company_id,
            target.name AS target_company_name,
            hop_distance,
            [relationship IN relationships(path) | coalesce(relationship.dependency_weight, $default_weight)] AS dependency_weights,
            [node IN nodes(path) | {{company_id: node.company_id, name: node.name}}] AS path_nodes
        ORDER BY hop_distance, target.company_id, affected_company_id
        """
        with self.connection.driver.session() as session:
            records = list(session.run(query, event_id=event_id, default_weight=DEFAULT_DEPENDENCY_WEIGHT))
        return [dict(record) for record in records]

    def get_company_event_exposure(self, company_id: str, *, max_hops: int = 3) -> list[dict]:
        if max_hops not in {1, 2, 3}:
            raise ValueError("max_hops must be between 1 and 3.")
        query = f"""
        MATCH (event:Event)-[:AFFECTS]->(source:Company)
        MATCH path = (source)-[:SUPPLIES*0..{max_hops}]->(target:Company {{company_id: $company_id}})
        WHERE all(node IN nodes(path) WHERE single(other IN nodes(path) WHERE other = node))
        WITH event, source, target, path, length(path) AS hop_distance
        RETURN DISTINCT event.event_id AS event_id, event.event_type AS event_type, event.severity AS severity,
            event.timestamp AS timestamp, event.source AS source, event.confidence AS confidence,
            event.description AS description, source.company_id AS affected_company_id,
            source.name AS affected_company_name, target.company_id AS target_company_id,
            target.name AS target_company_name, hop_distance,
            [relationship IN relationships(path) | coalesce(relationship.dependency_weight, $default_weight)] AS dependency_weights,
            [node IN nodes(path) | {{company_id: node.company_id, name: node.name}}] AS path_nodes
        ORDER BY timestamp DESC, event_id, hop_distance
        """
        with self.connection.driver.session() as session:
            records = list(session.run(query, company_id=company_id, default_weight=DEFAULT_DEPENDENCY_WEIGHT))
        return [dict(record) for record in records]
