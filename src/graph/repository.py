"""
Repository for persisting supply chain domain objects in Neo4j.
"""

import json

from src.events.models import SupplyChainEvent
from src.events.serialization import event_to_dict
from src.graph.connection import Neo4jConnection


class GraphRepository:
    """Handles persistence of domain objects in the Neo4j graph."""

    def __init__(self, connection: Neo4jConnection) -> None:
        self.connection = connection

    def save_event(self, event: SupplyChainEvent) -> None:
        """
        Persist a SupplyChainEvent as an Event node in Neo4j.
        """

        event_data = event_to_dict(event)

        query = """
        MERGE (event:Event {event_id: $event_id})
        SET
            event.event_type = $event_type,
            event.source = $source,
            event.timestamp = $timestamp,
            event.entity_id = $entity_id,
            event.severity = $severity,
            event.payload = $payload,
            event.created_at = $created_at
        """

        with self.connection.driver.session() as session:
            session.run(
                query,
                event_id=event_data["event_id"],
                event_type=event_data["event_type"],
                source=event_data["source"],
                timestamp=event_data["timestamp"],
                entity_id=event_data["entity_id"],
                severity=event_data["severity"],
                payload=json.dumps(event_data["payload"]),
                created_at=event_data["created_at"],
            )