from __future__ import annotations

from typing import Any

from src.graph.connection import Neo4jConnection
from src.graph.contracts import canonical_graph_id


class CompanyGraphRepository:
    """Read-only company and bounded graph queries for the public API."""

    def __init__(self, connection: Neo4jConnection) -> None:
        self.connection = connection

    @staticmethod
    def _json_safe(value: Any) -> Any:
        if isinstance(value, dict):
            return {key: CompanyGraphRepository._json_safe(item) for key, item in value.items()}
        if isinstance(value, list):
            return [CompanyGraphRepository._json_safe(item) for item in value]
        if hasattr(value, "iso_format"):
            return value.iso_format()
        if hasattr(value, "isoformat"):
            return value.isoformat()
        return value

    @staticmethod
    def _company_filter_params(*, search: str | None, industry_id: str | None, entity_type: str | None) -> dict[str, Any]:
        return {
            "search": search.strip() if search and search.strip() else None,
            "industry_id": industry_id.strip() if industry_id and industry_id.strip() else None,
            "entity_type": entity_type.strip() if entity_type and entity_type.strip() else None,
        }

    def list_companies(self, *, limit: int = 100, offset: int = 0, search: str | None = None, industry_id: str | None = None, entity_type: str | None = None) -> list[dict[str, Any]]:
        query = """
        MATCH (c:Company)
        OPTIONAL MATCH (c)-[:OPERATES_IN]->(i:Industry)
        WHERE ($search IS NULL OR
               toLower(coalesce(c.name, '')) CONTAINS toLower($search) OR
               toLower(coalesce(c.legal_name, '')) CONTAINS toLower($search) OR
               toLower(coalesce(c.company_id, '')) CONTAINS toLower($search))
          AND ($industry_id IS NULL OR i.industry_id = $industry_id)
          AND ($entity_type IS NULL OR c.entity_type = $entity_type)
        RETURN DISTINCT c.company_id AS company_id, c.name AS name, c.legal_name AS legal_name,
               c.entity_type AS entity_type, i.industry_id AS industry_id
        ORDER BY toLower(coalesce(c.name, c.company_id))
        SKIP $offset LIMIT $limit
        """
        params = self._company_filter_params(search=search, industry_id=industry_id, entity_type=entity_type)
        params.update({"limit": limit, "offset": offset})
        with self.connection.driver.session() as session:
            return [self._json_safe(record.data()) for record in session.run(query, **params)]

    def count_companies(self, *, search: str | None = None, industry_id: str | None = None, entity_type: str | None = None) -> int:
        query = """
        MATCH (c:Company)
        OPTIONAL MATCH (c)-[:OPERATES_IN]->(i:Industry)
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
                  WHERE value IS NOT NULL AND toLower(toString(value)) CONTAINS toLower($search_query))
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
            result = session.run(query, labels=labels, search_query=query_text.strip(), limit=limit)
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
        LIMIT 1
        """
        with self.connection.driver.session() as session:
            record = session.run(query, company_id=company_id).single()
            return self._json_safe(record.data()) if record else None

    def get_company_network(self, company_id: str, *, depth: int = 2) -> dict[str, Any] | None:
        existence_query = "MATCH (c:Company {company_id: $company_id}) RETURN c LIMIT 1"
        path_query = """
        MATCH path=(c:Company {company_id: $company_id})-[*1..3]-(n)
        WHERE length(path) <= $depth
          AND all(rel IN relationships(path) WHERE type(rel) IN $relationship_types)
        RETURN path
        LIMIT 500
        """
        relationship_types = ["SUPPLIES", "DEPENDS_ON", "OPERATES", "OWNS", "USES", "PRODUCES", "OPERATES_IN", "LOCATED_IN", "AFFECTS", "OCCURS_AT"]
        with self.connection.driver.session() as session:
            if session.run(existence_query, company_id=company_id).single() is None:
                return None
            records = session.run(path_query, company_id=company_id, depth=depth, relationship_types=relationship_types)
            nodes: dict[str, dict[str, Any]] = {}
            relationships: dict[str, dict[str, Any]] = {}
            for record in records:
                path = record["path"]
                for node in path.nodes:
                    labels = list(node.labels)
                    label = labels[0] if labels else "Node"
                    props = self._json_safe(dict(node))
                    node_id = canonical_graph_id(label, props, node.element_id)
                    name = str(props.get("name") or props.get("legal_name") or props.get("company_id") or props.get("facility_id") or props.get("event_id") or node_id)
                    nodes[node_id] = {"id": node_id, "label": label, "name": name, "properties": props}
                for rel in path.relationships:
                    start = rel.start_node
                    end = rel.end_node
                    start_labels = list(start.labels)
                    end_labels = list(end.labels)
                    source = canonical_graph_id(start_labels[0] if start_labels else "Node", dict(start), start.element_id)
                    target = canonical_graph_id(end_labels[0] if end_labels else "Node", dict(end), end.element_id)
                    rel_id = f"{source}|{rel.type}|{target}|{rel.element_id}"
                    relationships[rel_id] = {"id": rel_id, "source": source, "target": target, "relationship_type": rel.type, "properties": self._json_safe(dict(rel))}
            if not nodes:
                company = self.get_company(company_id)
                if company is not None:
                    node_id = canonical_graph_id("Company", company, company_id)
                    nodes[node_id] = {"id": node_id, "label": "Company", "name": str(company.get("name") or company_id), "properties": company}
            return {"company_id": company_id, "depth": depth, "nodes": list(nodes.values()), "relationships": list(relationships.values())}
