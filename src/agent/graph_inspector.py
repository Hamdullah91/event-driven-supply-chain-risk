from __future__ import annotations

from datetime import date, datetime
from typing import Any

from neo4j import Driver
from neo4j.graph import Node, Path, Relationship

from src.agent.cypher_validator import CypherValidator
from src.agent.evidence import (
    EvidenceBundle,
    EventEvidence,
    GraphNodeEvidence,
    GraphPathEvidence,
    GraphRelationshipEvidence,
)
from src.agent.models import CypherProposal
from src.events.types import EventSeverity


class GraphInspector:
    """Execute validated read-only Cypher and normalize graph evidence for reasoning."""

    def __init__(self, driver: Driver, *, database: str | None = None) -> None:
        self.driver = driver
        self.database = database

    def inspect(
        self,
        *,
        question: str,
        proposal: CypherProposal,
        validator: CypherValidator | None = None,
    ) -> EvidenceBundle:
        (validator or CypherValidator()).ensure_safe(proposal)
        records = self._execute_query(proposal)
        paths = self._extract_paths(records)
        node_refs = {node.ref for path in paths for node in path.nodes}
        events = self._fetch_events(node_refs)

        warnings: list[str] = []
        if not paths:
            warnings.append(
                "The validated query returned no explicit graph Path objects; "
                "multi-hop explainability is limited."
            )
        if not events:
            warnings.append(
                "No Event nodes were linked to entities in the retrieved paths."
            )

        return EvidenceBundle(
            question=question,
            cypher=proposal.cypher,
            query_results=[self._serialize_record(record) for record in records],
            paths=paths,
            events=events,
            warnings=warnings,
        )

    def _execute_query(self, proposal: CypherProposal) -> list[dict[str, Any]]:
        session_kwargs = {"database": self.database} if self.database else {}
        with self.driver.session(**session_kwargs) as session:
            result = session.run(proposal.cypher, proposal.parameters)
            return [dict(record) for record in result]

    def _extract_paths(self, records: list[dict[str, Any]]) -> list[GraphPathEvidence]:
        serialized: list[GraphPathEvidence] = []
        seen: set[str] = set()

        for record in records:
            for value in record.values():
                for path in self._find_paths(value):
                    if self._has_repeated_nodes(path):
                        continue
                    key = self._path_key(path)
                    if key in seen:
                        continue
                    seen.add(key)
                    hop_count = len(path.relationships)
                    if hop_count > 3:
                        continue
                    serialized.append(self._serialize_path(path, len(serialized) + 1))
        return serialized

    def _find_paths(self, value: Any) -> list[Path]:
        if isinstance(value, Path):
            return [value]
        if isinstance(value, dict):
            return [path for nested in value.values() for path in self._find_paths(nested)]
        if isinstance(value, (list, tuple)):
            return [path for nested in value for path in self._find_paths(nested)]
        return []

    def _serialize_path(self, path: Path, index: int) -> GraphPathEvidence:
        return GraphPathEvidence(
            path_id=f"P{index}",
            nodes=[self._serialize_node(node) for node in path.nodes],
            relationships=[self._serialize_relationship(rel) for rel in path.relationships],
            hop_count=len(path.relationships),
        )

    def _serialize_node(self, node: Node) -> GraphNodeEvidence:
        return GraphNodeEvidence(
            ref=node.element_id,
            labels=sorted(node.labels),
            properties={key: self._serialize_value(value) for key, value in dict(node).items()},
        )

    def _serialize_relationship(self, relationship: Relationship) -> GraphRelationshipEvidence:
        return GraphRelationshipEvidence(
            ref=relationship.element_id,
            relationship_type=type(relationship).__name__,
            start_node_ref=relationship.start_node.element_id if relationship.start_node else None,
            end_node_ref=relationship.end_node.element_id if relationship.end_node else None,
            properties={key: self._serialize_value(value) for key, value in dict(relationship).items()},
        )

    def _fetch_events(self, node_refs: set[str]) -> list[EventEvidence]:
        if not node_refs:
            return []

        cypher = """
        MATCH (entity)
        WHERE elementId(entity) IN $node_refs
        MATCH (event:Event)-[link:AFFECTS|OCCURS_AT]->(entity)
        RETURN DISTINCT event,
               type(link) AS linkage_type,
               elementId(entity) AS linked_entity_ref,
               properties(entity) AS linked_entity_properties
        """
        session_kwargs = {"database": self.database} if self.database else {}
        with self.driver.session(**session_kwargs) as session:
            result = session.run(cypher, node_refs=sorted(node_refs))
            events: list[EventEvidence] = []
            seen: set[tuple[str, str | None]] = set()
            for record in result:
                event: Node = record["event"]
                key = (event.element_id, record["linked_entity_ref"])
                if key in seen:
                    continue
                seen.add(key)
                props = dict(event)
                entity_props = dict(record["linked_entity_properties"] or {})
                events.append(
                    EventEvidence(
                        ref=event.element_id,
                        event_id=self._optional_str(props.get("event_id")),
                        event_type=self._optional_str(props.get("event_type")),
                        timestamp=self._optional_str(props.get("timestamp")),
                        severity=self._optional_severity(props.get("severity")),
                        confidence=self._optional_float(props.get("confidence")),
                        description=self._optional_str(props.get("description")),
                        source=self._optional_str(props.get("source")),
                        linked_entity_ref=record["linked_entity_ref"],
                        linked_entity_id=self._first_present(
                            entity_props,
                            "company_id",
                            "facility_id",
                            "material_id",
                            "product_id",
                            "country_id",
                            "id",
                        ),
                        linked_entity_name=self._first_present(
                            entity_props,
                            "name",
                            "company_name",
                            "facility_name",
                            "material_name",
                            "product_name",
                            "id",
                        ),
                        linkage_type=record["linkage_type"],
                    )
                )
            return events

    def _serialize_record(self, record: dict[str, Any]) -> dict[str, Any]:
        return {key: self._serialize_value(value) for key, value in record.items()}

    def _serialize_value(self, value: Any) -> Any:
        if isinstance(value, Node):
            return self._serialize_node(value).model_dump()
        if isinstance(value, Relationship):
            return self._serialize_relationship(value).model_dump()
        if isinstance(value, Path):
            return self._serialize_path(value, 0).model_dump()
        if isinstance(value, dict):
            return {key: self._serialize_value(item) for key, item in value.items()}
        if isinstance(value, (list, tuple)):
            return [self._serialize_value(item) for item in value]
        if isinstance(value, (datetime, date)):
            return value.isoformat()
        return value

    @staticmethod
    def _optional_float(value: Any) -> float | None:
        if value is None:
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _optional_severity(value: Any) -> EventSeverity | None:
        if value is None:
            return None
        try:
            return EventSeverity(str(value).strip().lower())
        except ValueError:
            return EventSeverity.UNKNOWN

    @staticmethod
    def _optional_str(value: Any) -> str | None:
        return None if value is None else str(value)

    @staticmethod
    def _first_present(properties: dict[str, Any], *keys: str) -> str | None:
        for key in keys:
            value = properties.get(key)
            if value not in (None, ""):
                return str(value)
        return None

    @staticmethod
    def _has_repeated_nodes(path: Path) -> bool:
        node_ids = [node.element_id for node in path.nodes]
        return len(node_ids) != len(set(node_ids))

    @staticmethod
    def _path_key(path: Path) -> str:
        relationship_ids = [relationship.element_id for relationship in path.relationships]
        if relationship_ids:
            return "|".join(relationship_ids)
        return "nodes:" + "|".join(node.element_id for node in path.nodes)
