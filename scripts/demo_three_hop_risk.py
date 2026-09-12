from __future__ import annotations

from src.graph.connection import Neo4jConnection
from src.risk.repository import RiskRepository
from src.risk.service import RiskPropagationService


EVENT_ID = "day41-three-hop-validation-event"
SOURCE_COMPANY_ID = "asml"
TEMP_COMPANY_ID = "day41-validation-customer"
EVENT_SEVERITY = "high"


def create_validation_fixture(connection: Neo4jConnection) -> None:
    """Create the temporary event and third-hop customer for Day 41."""

    query = """
    MATCH (source:Company {company_id: $source_company_id})
    MATCH (nvidia:Company {company_id: 'nvidia'})

    MERGE (event:Event {event_id: $event_id})
    SET
        event.event_type = 'supply_disruption',
        event.source = 'day41_validation',
        event.timestamp = datetime(),
        event.entity_id = source.company_id,
        event.severity = $severity,
        event.payload = '{}'

    MERGE (event)-[affects:AFFECTS]->(source)
    SET
        affects.confidence = 1.0,
        affects.link_method = 'day41_validation',
        affects.linked_at = datetime()

    MERGE (customer:Company {company_id: $temp_company_id})
    SET customer.name = 'Day 41 Validation Customer'

    MERGE (nvidia)-[supplies:SUPPLIES]->(customer)
    SET
        supplies.dependency_weight = 1.0,
        supplies.source = 'day41_validation'

    RETURN source.name AS source_company_name
    """

    with connection.driver.session() as session:
        record = session.run(
            query,
            event_id=EVENT_ID,
            source_company_id=SOURCE_COMPANY_ID,
            temp_company_id=TEMP_COMPANY_ID,
            severity=EVENT_SEVERITY,
        ).single()

    if record is None:
        raise RuntimeError(
            "Day 41 validation requires ASML and NVIDIA to exist in Neo4j. "
            "Seed the baseline graph first."
        )


def delete_validation_fixture(connection: Neo4jConnection) -> None:
    """Remove only nodes created specifically for the Day 41 demo."""

    query = """
    OPTIONAL MATCH (event:Event {event_id: $event_id})
    DETACH DELETE event
    WITH 1 AS ignored
    OPTIONAL MATCH (customer:Company {company_id: $temp_company_id})
    DETACH DELETE customer
    """

    with connection.driver.session() as session:
        session.run(
            query,
            event_id=EVENT_ID,
            temp_company_id=TEMP_COMPANY_ID,
        ).consume()


def main() -> None:
    connection = Neo4jConnection()

    try:
        delete_validation_fixture(connection)
        create_validation_fixture(connection)

        service = RiskPropagationService(RiskRepository(connection))
        exposures = service.calculate_three_hop_exposure(EVENT_ID)

        print("\n=== DAY 41 THREE-HOP RISK ===")

        if not exposures:
            print("No three-hop downstream SUPPLIES path was found from ASML.")
            print(
                "Expected validation topology: "
                "ASML -> TSMC -> NVIDIA -> Day 41 Validation Customer."
            )
            return

        for exposure in exposures:
            print(f"Event: {exposure.event_id}")
            print(f"Severity: {exposure.event_severity}")
            print(
                f"Path: {exposure.source_company_name}"
                f" -> {exposure.hop_1_company_name}"
                f" -> {exposure.hop_2_company_name}"
                f" -> {exposure.hop_3_company_name}"
            )
            print(f"Hop: {exposure.hop_distance}")
            print(f"Initial risk: {exposure.initial_risk:.3f}")
            print(
                "Dependency weights: "
                f"{exposure.hop_1_weight:.3f} "
                f"({exposure.hop_1_weight_source}), "
                f"{exposure.hop_2_weight:.3f} "
                f"({exposure.hop_2_weight_source}), "
                f"{exposure.hop_3_weight:.3f} "
                f"({exposure.hop_3_weight_source})"
            )
            print(f"Path dependency: {exposure.path_dependency:.3f}")
            print(f"Distance decay: {exposure.distance_decay:.3f}")
            print(f"Propagated risk: {exposure.propagated_risk:.3f}")
            print()
    finally:
        delete_validation_fixture(connection)
        connection.close()


if __name__ == "__main__":
    main()
