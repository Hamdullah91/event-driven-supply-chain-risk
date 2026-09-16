from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from neo4j.graph import Node, Path, Relationship

from src.graph.connection import Neo4jConnection


STRUCTURAL_RELATIONSHIPS = (
    "SUPPLIES",
    "DEPENDS_ON",
    "OPERATES",
    "OWNS",
    "USES",
    "PRODUCES",
    "LOCATED_IN",
    "OPERATES_IN",
)


class CompanyGraphRepository:
    """Read-only Neo4j repository for company and network queries."""

    def __init__(self, connection: Neo4jConnection) -> None:
        self.connection = connection

    def list_companies(
        self,
        *,
        limit: int = 100,
        offset: int = 0,
        search: str | None = None,
        industry_id: str | None = None,
        entity_type: str | None = None,
    ) -> list[dict[str, Any]]:
        query = """
        MATCH (c:Company)
        OPTIONAL MATCH (c)-[:OPERATES_IN]->(i:Industry)
        WITH c, i
        WHERE ($search IS NULL OR
               toLower(coalesce(c.name, '')) CONTAINS toLower($search) OR
               toLower(coalesce(c.legal_name, '')) CONTAINS toLower($search) OR
               toLower(coalesce(c.company_id, '')) CONTAINS toLower($search))
          AND ($industry_id IS NULL OR i.industry_id = $industry_id)
          AND ($entity_type IS NULL OR c.entity_type = $entity_type)
        RETURN
            c.company_id AS company_id,
            c.name AS name,
            c.legal_name AS legal_name,
            c.entity_type AS entity_type,
            i.industry_id AS industry_id
        ORDER BY toLower(coalesce(c.name, c.company_id)), c.company_id
        SKIP $offset
        LIMIT $limit
        """
        params = self._company_filter_params(
            search=search,
            industry_id=industry_id,
            entity_type=entity_type,
        )
        params.update(limit=limit, offset=offset)
        with self.connection.driver.session() as session:
            result = session.run(query, **params)
            return [self._json_safe(record.data()) for record in result]

    def count_companies(
        self,
        *,
        search: str | None = None,
        industry_id: str | None = None,
        entity_type: str | None = None,
    ) -> int:
        query = """
        MATCH (c:Company)
        OPTIONAL MATCH (c)-[:OPERATES_IN]->(i:Industry)
        WITH c, i
        WHERE ($search IS NULL OR
               toLower(coalesce(c.name, '')) CONTAINS toLower($search) OR
               toLower(coalesce(c.legal_name, '')) CONTAINS toLower($search) OR
               toLower(coalesce(c.company_id, '')) CONTAINS toLower($search))
          AND ($industry_id IS NULL OR i.industry_id = $industry_id)
          AND ($entity_type IS NULL OR c.entity_type = $entity_type)
        RETURN count(DISTINCT c) AS count
        """
        params = self._company_filter_params(search=search, industry_id=industry_id, entity_type=entity_type)
        with self.connection.driver.session() as session:
            record = session.run(query, **params).single()
        return int(record["count"]) if record else 0

    def search_entities(self, query_text: str, *, limit: int = 25) -> list[dict[str, Any]]:
        query = """
        MATCH (n)
        WHERE any(label IN labels(n) WHERE label IN $labels)
          AND any(value IN [n.name, n.legal_name, n.company_id, n.facility_id,
                            n.product_id, n.material_id, n.technology_id,
                            n.industry_id, n.location_id, n.country_id, n.event_id]
                  WHERE value IS NOT NULL AND toLower(toString(value)) CONTAINS toLower($query))
        WITH n, head([label IN labels(n) WHERE label IN $labels]) AS label
        RETURN label,
               coalesce(n.company_id, n.facility_id, n.product_id, n.material_id,
                        n.technology_id, n.industry_id, n.location_id, n.country_id,
                        n.event_id, elementId(n)) AS entity_id,
               coalesce(n.name, n.legal_name, n.company_id, n.facility_id,
                        n.product_id, n.material_id, n.technology_id, n.industry_id,
                        n.location_id, n.country_id, n.event_id) AS name,
               properties(n) AS properties
        ORDER BY toLower(toString(name))
        LIMIT $limit
        """
        labels = ["Company", "Facility", "Product", "Material", "Technology", "Industry", "Location", "Country", "Event"]
        with self.connection.driver.session() as session:
            result = session.run(query, labels=labels, query=query_text.strip(), limit=limit)
            return [self._json_safe(record.data()) for record in result]

    def get_company(self, company_id: str) -> dict[str, Any] | None:
        query = """
        MATCH (c:Company {company_id: $company_id})
        OPTIONAL MATCH (c)-[:OPERATES_IN]->(i:Industry)
        OPTIONAL MATCH (c)-[:OPERATES]->(f:Facility)
        WITH c, i, collect(DISTINCT f.name) AS facilities
        OPTIONAL MATCH (c)-[:PRODUCES]->(p:Product)
        WITH c, i, facilities, collect(DISTINCT p.name) AS products
        OPTIONAL MATCH (c)-[:USES]->(m:Material)
        WITH c, i, facilities, products, collect(DISTINCT m.name) AS materials
        OPTIONAL MATCH (c)-[:USES]->(t:Technology)
        RETURN c.company_id AS company_id, c.name AS name, c.legal_name AS legal_name,
               c.entity_type AS entity_type, c.seed_source AS seed_source,
               i.industry_id AS industry_id, facilities, products, materials,
               collect(DISTINCT t.name) AS technologies
        """
        with self.connection.driver.session() as session:
            record = session.run(query, company_id=company_id).single()
        if record is None:
            return None
        data = self._json_safe(record.data())
        for key in ("facilities", "products", "materials", "technologies"):
            data[key] = sorted(value for value in data.get(key, []) if value)
        return data

    def company_exists(self, company_id: str) -> bool:
        query = "MATCH (c:Company {company_id: $company_id}) RETURN count(c) > 0 AS exists"
        with self.connection.driver.session() as session:
            record = session.run(query, company_id=company_id).single()
        return bool(record and record["exists"])

    def get_company_network(self, company_id: str, *, depth: int = 2) -> dict[str, Any] | None:
        if depth not in {1, 2, 3}:
            raise ValueError("depth must be between 1 and 3")
        root_query = "MATCH (root:Company {company_id: $company_id}) RETURN root"
        relationship_pattern = "|".join(STRUCTURAL_RELATIONSHIPS)
        path_queries = {hop: f"""
            MATCH p=(root:Company {{company_id: $company_id}})-[:{relationship_pattern}*1..{hop}]-(connected)
            WHERE all(node IN nodes(p) WHERE single(other IN nodes(p) WHERE other = node))
            RETURN p
            """ for hop in (1, 2, 3)}
        with self.connection.driver.session() as session:
            root_record = session.run(root_query, company_id=company_id).single()
            if root_record is None:
                return None
            result = list(session.run(path_queries[depth], company_id=company_id))
        nodes: dict[str, dict[str, Any]] = {}
        relationships: dict[str, dict[str, Any]] = {}
        self._consume_node(root_record["root"], nodes)
        for record in result:
            self._consume_path(record["p"], nodes=nodes, relationships=relationships)
        return {"company_id": company_id, "depth": depth, "nodes": list(nodes.values()), "relationships": list(relationships.values())}

    @staticmethod
    def _company_filter_params(*, search: str | None, industry_id: str | None, entity_type: str | None) -> dict[str, str | None]:
        return {
            "search": search.strip() if search and search.strip() else None,
            "industry_id": industry_id.strip() if industry_id and industry_id.strip() else None,
            "entity_type": entity_type.strip() if entity_type and entity_type.strip() else None,
        }

    @classmethod
    def _consume_path(cls, path: Path, *, nodes: dict[str, dict[str, Any]], relationships: dict[str, dict[str, Any]]) -> None:
        for node in path.nodes:
            cls._consume_node(node, nodes)
        for relationship in path.relationships:
            relationship_id = relationship.element_id
            relationships[relationship_id] = {"id": relationship_id, "source": cls._node_graph_id(relationship.start_node), "target": cls._node_graph_id(relationship.end_node), "type": relationship.type, "properties": cls._json_safe(dict(relationship))}

    @classmethod
    def _consume_node(cls, node: Node, nodes: dict[str, dict[str, Any]]) -> None:
        graph_id = cls._node_graph_id(node)
        properties = cls._json_safe(dict(node))
        label = sorted(node.labels)[0] if node.labels else "Unknown"
        name = properties.get("name") or properties.get("legal_name") or properties.get("company_id") or properties.get("facility_id") or properties.get("product_id") or properties.get("material_id") or properties.get("technology_id") or properties.get("industry_id") or properties.get("location_id") or properties.get("country_id") or graph_id
        nodes[graph_id] = {"id": graph_id, "label": label, "name": str(name), "properties": properties}

    @staticmethod
    def _node_graph_id(node: Node) -> str:
        properties = dict(node)
        labels = sorted(node.labels)
        label = labels[0] if labels else "Unknown"
        identity_keys = {"Company": "company_id", "Facility": "facility_id", "Product": "product_id", "Material": "material_id", "Technology": "technology_id", "Industry": "industry_id", "Location": "location_id", "Country": "country_id", "Event": "event_id"}
        key = identity_keys.get(label)
        if key and properties.get(key):
            return f"{label.lower()}:{properties[key]}"
        return f"{label.lower()}:{node.element_id}"

    @classmethod
    def _json_safe(cls, value: Any) -> Any:
        if value is None or isinstance(value, (str, int, float, bool)):
            return value
        if isinstance(value, Mapping):
            return {str(key): cls._json_safe(item) for key, item in value.items()}
        if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
            return [cls._json_safe(item) for item in value]
        to_native = getattr(value, "to_native", None)
        if callable(to_native):
            return cls._json_safe(to_native())
        isoformat = getattr(value, "isoformat", None)
        if callable(isoformat):
            return isoformat()
        return str(value)
