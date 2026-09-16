from __future__ import annotations

import json
from typing import Any

from src.graph.connection import Neo4jConnection


class EventReadRepository:
    """Read-only repository for persisted Event nodes."""

    def __init__(self, connection: Neo4jConnection) -> None:
        self.connection = connection

    @staticmethod
    def _normalize_event(properties: dict[str, Any]) -> dict[str, Any]:
        event = dict(properties)
        payload = event.get("payload")
        if isinstance(payload, str):
            try:
                event["payload"] = json.loads(payload)
            except json.JSONDecodeError:
                event["payload"] = {"raw": payload}
        elif payload is None:
            event["payload"] = {}
        return event

    def list_events(self, *, limit: int, offset: int) -> list[dict[str, Any]]:
        query = """
        MATCH (event:Event)
        RETURN properties(event) AS event
        ORDER BY event.timestamp DESC, event.created_at DESC, event.event_id ASC
        SKIP $offset
        LIMIT $limit
        """
        with self.connection.driver.session() as session:
            records = session.run(query, limit=limit, offset=offset)
            return [self._normalize_event(dict(record["event"])) for record in records]

    def count_events(self) -> int:
        query = """
        MATCH (event:Event)
        RETURN count(event) AS count
        """
        with self.connection.driver.session() as session:
            record = session.run(query).single()
        return int(record["count"]) if record else 0

    def get_event(self, event_id: str) -> dict[str, Any] | None:
        query = """
        MATCH (event:Event {event_id: $event_id})
        RETURN properties(event) AS event
        """
        with self.connection.driver.session() as session:
            record = session.run(query, event_id=event_id).single()
        if record is None:
            return None
        return self._normalize_event(dict(record["event"]))
