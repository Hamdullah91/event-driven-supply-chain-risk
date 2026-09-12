from __future__ import annotations

from typing import Generator

import pytest

from src.graph.connection import Neo4jConnection
from src.risk.repository import RiskRepository
from src.risk.service import RiskPropagationService


EVENT_ID = "day44-risk-integration-event"
SOURCE_ID = "day44-source"
HOP_1_ID = "day44-hop-1"
HOP_2_ID = "day44-hop-2"
HOP_3_ID = "day44-hop-3"


@pytest.fixture
def connection() -> Generator[Neo4jConnection, None, None]:
    connection = Neo4jConnection()
    connection.verify_connection()

    try:
        yield connection
    finally:
        connection.close()


def _cleanup_day44_graph(connection: Neo4jConnection) -> None:
    with connection.driver.session() as session:
        session.run(
            """
            MATCH (node)
            WHERE node.day44_risk_test = true
            DETACH DELETE node
            """
        ).consume()


def _seed_day44_graph(connection: Neo4jConnection) -> None:
    _cleanup_day44_graph(connection)

    with connection.driver.session() as session:
        session.run(
            """
            CREATE (event:Event {
                event_id: $event_id,
                event_type: 'FACILITY_OUTAGE',
                severity: 'high',
                day44_risk_test: true
            })
            CREATE (source:Company {
                company_id: $source_id,
                name: 'Day 44 Source Supplier',
                day44_risk_test: true
            })
            CREATE (hop1:Company {
                company_id: $hop_1_id,
                name: 'Day 44 Manufacturer',
                day44_risk_test: true
            })
            CREATE (hop2:Company {
                company_id: $hop_2_id,
                name: 'Day 44 Integrator',
                day44_risk_test: true
            })
            CREATE (hop3:Company {
                company_id: $hop_3_id,
                name: 'Day 44 Customer',
                day44_risk_test: true
            })
            CREATE (event)-[:AFFECTS]->(source)
            CREATE (source)-[:SUPPLIES {dependency_weight: 0.90}]->(hop1)
            CREATE (hop1)-[:SUPPLIES {dependency_weight: 0.75}]->(hop2)
            CREATE (hop2)-[:SUPPLIES {dependency_weight: 0.60}]->(hop3)
            """,
            event_id=EVENT_ID,
            source_id=SOURCE_ID,
            hop_1_id=HOP_1_ID,
            hop_2_id=HOP_2_ID,
            hop_3_id=HOP_3_ID,
        ).consume()


def test_neo4j_traversal_matches_risk_mathematics(
    connection: Neo4jConnection,
) -> None:
    """Prove graph traversal and deterministic propagation agree end to end."""
    _seed_day44_graph(connection)

    try:
        service = RiskPropagationService(RiskRepository(connection))

        one_hop = service.calculate_one_hop_exposure(EVENT_ID)
        two_hop = service.calculate_two_hop_exposure(EVENT_ID)
        three_hop = service.calculate_three_hop_exposure(EVENT_ID)

        assert len(one_hop) == 1
        assert len(two_hop) == 1
        assert len(three_hop) == 1

        assert one_hop[0].target_company_id == HOP_1_ID
        assert two_hop[0].hop_2_company_id == HOP_2_ID
        assert three_hop[0].hop_3_company_id == HOP_3_ID

        # severity='high' -> initial risk 0.75
        assert one_hop[0].initial_risk == pytest.approx(0.75)
        assert two_hop[0].initial_risk == pytest.approx(0.75)
        assert three_hop[0].initial_risk == pytest.approx(0.75)

        # R = R0 * product(weights) * 0.70 ** (h - 1)
        assert one_hop[0].propagated_risk == pytest.approx(0.675)
        assert two_hop[0].propagated_risk == pytest.approx(0.354375)
        assert three_hop[0].propagated_risk == pytest.approx(0.1488375)

        assert (
            one_hop[0].propagated_risk
            > two_hop[0].propagated_risk
            > three_hop[0].propagated_risk
        )

        assert two_hop[0].path_dependency == pytest.approx(0.675)
        assert three_hop[0].path_dependency == pytest.approx(0.405)
        assert two_hop[0].distance_decay == pytest.approx(0.70)
        assert three_hop[0].distance_decay == pytest.approx(0.49)

    finally:
        _cleanup_day44_graph(connection)
