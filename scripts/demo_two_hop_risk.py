from __future__ import annotations

from src.graph.connection import Neo4jConnection
from src.risk.repository import RiskRepository
from src.risk.service import RiskPropagationService


EVENT_ID = "day40-two-hop-validation-event"
SOURCE_COMPANY_ID = "asml"
EVENT_SEVERITY = "high"


def create_validation_event(connection: Neo4jConnection) -> None:
    """Create a temporary Event attached to ASML for Day 40 validation."""

    query = """
    MATCH (source:Company {company_id: $company_id})

    MERGE (event:Event {event_id: $event_id})
    SET
        event.event_type = 'supply_disruption',
        event.source = 'day40_validation',
        event.timestamp = datetime(),
        event.entity_id = source.company_id,
        event.severity = $severity,
        event.payload = '{}'

    MERGE (event)-[relationship:AFFECTS]->(source)
    SET
        relationship.confidence = 1.0,
        relationship.link_method = 'day40_validation',
        relationship.linked_at = datetime()

    RETURN source.name AS source_company_name
    """

    with connection.driver.session() as session:
        record = session.run(
            query,
            event_id=EVENT_ID,
            company_id=SOURCE_COMPANY_ID,
            severity=EVENT_SEVERITY,
        ).single()

    if record is None:
        raise RuntimeError(
            "Day 40 validation requires Company(company_id='asml') "
            "to exist in Neo4j. Seed the baseline graph first."
        )


def delete_validation_event(connection: Neo4jConnection) -> None:
    """Remove only the temporary Day 40 validation Event."""

    query = """
    MATCH (event:Event {event_id: $event_id})
    DETACH DELETE event
    """

    with connection.driver.session() as session:
        session.run(query, event_id=EVENT_ID).consume()


def main() -> None:
    connection = Neo4jConnection()

    try:
        # Ensure a stale validation event from an interrupted prior run
        # cannot affect the result.
        delete_validation_event(connection)
        create_validation_event(connection)

        repository = RiskRepository(connection)
        service = RiskPropagationService(repository)

        exposures = service.calculate_two_hop_exposure(EVENT_ID)

        print("\n=== DAY 40 TWO-HOP RISK ===")

        if not exposures:
            print(
                "No two-hop downstream SUPPLIES path was found from ASML."
            )
            print(
                "Expected verified topology: ASML -> TSMC -> NVIDIA."
            )
            return

        for exposure in exposures:
            print(f"Event: {exposure.event_id}")
            print(f"Severity: {exposure.event_severity}")
            print(
                f"Path: {exposure.source_company_name}"
                f" -> {exposure.hop_1_company_name}"
                f" -> {exposure.hop_2_company_name}"
            )
            print(f"Hop: {exposure.hop_distance}")
            print(f"Initial risk: {exposure.initial_risk}")
            print(
                "Dependency weights: "
                f"{exposure.hop_1_weight} "
                f"({exposure.hop_1_weight_source}), "
                f"{exposure.hop_2_weight} "
                f"({exposure.hop_2_weight_source})"
            )
            print(f"Path dependency: {exposure.path_dependency}")
            print(f"Distance decay: {exposure.distance_decay}")
            print(f"Propagated risk: {exposure.propagated_risk}")
            print()

    finally:
        delete_validation_event(connection)
        connection.close()


if __name__ == "__main__":
    main()
