from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Generator

import pytest

from src.events.models import SupplyChainEvent
from src.events.types import EventSeverity, EventType
from src.graph.connection import Neo4jConnection
from src.graph.repository import GraphRepository


@pytest.fixture
def connection() -> Generator[
    Neo4jConnection,
    None,
    None,
]:
    connection = Neo4jConnection()

    connection.verify_connection()

    try:
        yield connection
    finally:
        connection.close()


def test_connection(
    connection: Neo4jConnection,
) -> None:
    """Verify that Neo4j is reachable and basic CRUD works."""

    with connection.driver.session() as session:
        create_result = session.run(
            """
            CREATE (company:Company {
                name: $name,
                test: true
            })
            RETURN company.name AS name
            """,
            name="Test Semiconductor Corp",
        )

        created_record = create_result.single()

        if created_record is None:
            raise RuntimeError(
                "Neo4j did not return the created node."
            )

        assert (
            created_record["name"]
            == "Test Semiconductor Corp"
        )

        read_result = session.run(
            """
            MATCH (company:Company {
                name: $name,
                test: true
            })
            RETURN company.name AS name
            """,
            name="Test Semiconductor Corp",
        )

        companies = [
            record["name"]
            for record in read_result
        ]

        assert (
            "Test Semiconductor Corp"
            in companies
        )

        session.run(
            """
            MATCH (company:Company {
                name: $name,
                test: true
            })
            DELETE company
            """,
            name="Test Semiconductor Corp",
        )


def test_event_repository(
    connection: Neo4jConnection,
) -> None:
    """Verify that GraphRepository can persist a SupplyChainEvent."""

    repository = GraphRepository(
        connection
    )

    event = SupplyChainEvent(
        event_type=(
            EventType.SUPPLY_DISRUPTION
        ),
        source="test",
        timestamp=datetime.now(
            timezone.utc
        ),
        entity_id="TEST-COMPANY-001",
        severity=EventSeverity.HIGH,
        payload={
            "description": (
                "Test supply disruption"
            ),
        },
    )

    repository.save_event(
        event
    )

    try:
        with connection.driver.session() as session:
            result = session.run(
                """
                MATCH (event:Event {
                    event_id: $event_id
                })
                RETURN
                    event.event_id AS event_id,
                    event.event_type AS event_type,
                    event.source AS source,
                    event.entity_id AS entity_id,
                    event.severity AS severity,
                    event.payload AS payload
                """,
                event_id=str(
                    event.event_id
                ),
            )

            record = result.single()

            assert record is not None

            assert (
                record["event_id"]
                == str(event.event_id)
            )

            assert (
                record["event_type"]
                == event.event_type.value
            )

            assert (
                record["source"]
                == event.source
            )

            assert (
                record["entity_id"]
                == event.entity_id
            )

            assert (
                record["severity"]
                == event.severity.value
            )

            stored_payload = json.loads(
                record["payload"]
            )

            assert (
                stored_payload
                == event.payload
            )

    finally:
        with connection.driver.session() as session:
            session.run(
                """
                MATCH (event:Event {
                    event_id: $event_id
                })
                DELETE event
                """,
                event_id=str(
                    event.event_id
                ),
            )