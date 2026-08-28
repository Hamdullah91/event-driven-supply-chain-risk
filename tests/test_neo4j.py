import json
from datetime import datetime, timezone

from src.events.models import SupplyChainEvent
from src.events.types import EventSeverity, EventType
from src.graph.connection import Neo4jConnection
from src.graph.repository import GraphRepository


def test_connection(connection: Neo4jConnection) -> None:
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
            raise RuntimeError("Neo4j did not return the created node.")

        print(f"Created company: {created_record['name']}")

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

        companies = [record["name"] for record in read_result]

        if "Test Semiconductor Corp" not in companies:
            raise RuntimeError("Test node could not be read from Neo4j.")

        print(f"Companies found: {companies}")

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

        print("Connection test data cleaned up.")


def test_event_repository(connection: Neo4jConnection) -> None:
    """Verify that GraphRepository can persist a SupplyChainEvent."""

    repository = GraphRepository(connection)

    event = SupplyChainEvent(
        event_type=EventType.SUPPLY_DISRUPTION,
        source="test",
        timestamp=datetime.now(timezone.utc),
        entity_id="TEST-COMPANY-001",
        severity=EventSeverity.HIGH,
        payload={
            "description": "Test supply disruption",
        },
    )

    repository.save_event(event)

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
                event_id=str(event.event_id),
            )

            record = result.single()

            if record is None:
                raise RuntimeError(
                    "Repository did not persist the event."
                )

            if record["event_id"] != str(event.event_id):
                raise RuntimeError("Stored event_id does not match.")

            if record["event_type"] != event.event_type.value:
                raise RuntimeError("Stored event_type does not match.")

            if record["source"] != event.source:
                raise RuntimeError("Stored source does not match.")

            if record["entity_id"] != event.entity_id:
                raise RuntimeError("Stored entity_id does not match.")

            if record["severity"] != event.severity.value:
                raise RuntimeError("Stored severity does not match.")

            stored_payload = json.loads(record["payload"])

            if stored_payload != event.payload:
                raise RuntimeError("Stored payload does not match.")

            print(f"Event persisted: {event.event_id}")

    finally:
        with connection.driver.session() as session:
            session.run(
                """
                MATCH (event:Event {
                    event_id: $event_id
                })
                DELETE event
                """,
                event_id=str(event.event_id),
            )

        print("Event test data cleaned up.")


def main() -> None:
    connection = Neo4jConnection()

    try:
        connection.verify_connection()
        print("Neo4j connection verified.")

        test_connection(connection)
        test_event_repository(connection)

        print("All Neo4j repository tests passed.")

    finally:
        connection.close()


if __name__ == "__main__":
    main()