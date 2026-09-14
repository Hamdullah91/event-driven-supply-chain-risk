from __future__ import annotations

from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient

from src.api.app import app
from src.api.dependencies import get_neo4j_connection
from src.graph.connection import Neo4jConnection


SOURCE_ID = "day47-live-source"
MIDDLE_ID = "day47-live-middle"
TARGET_ID = "day47-live-target"
UPSTREAM_EVENT_ID = "day47-live-event-upstream"
DIRECT_EVENT_ID = "day47-live-event-direct"


@pytest.fixture
def live_graph() -> Generator[None, None, None]:
    """Seed a temporary graph in the configured live Neo4j instance."""
    connection = Neo4jConnection()
    connection.verify_connection()

    cleanup_query = """
    MATCH (node)
    WHERE node.company_id IN $company_ids
       OR node.event_id IN $event_ids
    DETACH DELETE node
    """

    company_ids = [SOURCE_ID, MIDDLE_ID, TARGET_ID]
    event_ids = [UPSTREAM_EVENT_ID, DIRECT_EVENT_ID]

    try:
        with connection.driver.session() as session:
            session.run(
                cleanup_query,
                company_ids=company_ids,
                event_ids=event_ids,
            ).consume()

            session.run(
                """
                CREATE (source:Company {
                    company_id: $source_id,
                    name: 'Day 47 Live Source'
                })
                CREATE (middle:Company {
                    company_id: $middle_id,
                    name: 'Day 47 Live Middle'
                })
                CREATE (target:Company {
                    company_id: $target_id,
                    name: 'Day 47 Live Target'
                })
                CREATE (source)-[:SUPPLIES {
                    dependency_weight: 0.8
                }]->(middle)
                CREATE (middle)-[:SUPPLIES {
                    dependency_weight: 0.5
                }]->(target)
                CREATE (upstream:Event {
                    event_id: $upstream_event_id,
                    event_type: 'SUPPLY_DISRUPTION',
                    severity: 'high',
                    timestamp: '2026-09-14T10:00:00Z',
                    source: 'day47-live-test',
                    confidence: 1.0,
                    description: 'Temporary upstream disruption'
                })
                CREATE (direct:Event {
                    event_id: $direct_event_id,
                    event_type: 'FACILITY_OUTAGE',
                    severity: 'medium',
                    timestamp: '2026-09-14T11:00:00Z',
                    source: 'day47-live-test',
                    confidence: 1.0,
                    description: 'Temporary direct disruption'
                })
                CREATE (upstream)-[:AFFECTS]->(source)
                CREATE (direct)-[:AFFECTS]->(target)
                """,
                source_id=SOURCE_ID,
                middle_id=MIDDLE_ID,
                target_id=TARGET_ID,
                upstream_event_id=UPSTREAM_EVENT_ID,
                direct_event_id=DIRECT_EVENT_ID,
            ).consume()

        yield
    finally:
        with connection.driver.session() as session:
            session.run(
                cleanup_query,
                company_ids=company_ids,
                event_ids=event_ids,
            ).consume()
        connection.close()
        if get_neo4j_connection.cache_info().currsize:
            get_neo4j_connection().close()
            get_neo4j_connection.cache_clear()


def test_risk_apis_against_live_neo4j(live_graph: None) -> None:
    """Exercise repository Cypher, service math, and HTTP responses together."""
    with TestClient(app) as client:
        risk_response = client.get(f"/risk/{TARGET_ID}")
        assert risk_response.status_code == 200
        risk = risk_response.json()
        assert risk["company_id"] == TARGET_ID
        assert risk["contributing_event_count"] == 2
        assert risk["risk_score"] == pytest.approx(0.605)
        assert risk["risk_level"] == "HIGH"

        exposure_response = client.get(f"/risk/{TARGET_ID}/exposure")
        assert exposure_response.status_code == 200
        exposure = exposure_response.json()
        assert exposure["event_count"] == 2

        by_event = {
            item["event_id"]: item
            for item in exposure["exposures"]
        }
        direct = by_event[DIRECT_EVENT_ID]
        assert direct["hop_distance"] == 0
        assert direct["propagated_risk"] == pytest.approx(0.5)

        upstream = by_event[UPSTREAM_EVENT_ID]
        assert upstream["hop_distance"] == 2
        assert upstream["path_dependency"] == pytest.approx(0.4)
        assert upstream["distance_decay"] == pytest.approx(0.7)
        assert upstream["propagated_risk"] == pytest.approx(0.21)
        assert [node["company_id"] for node in upstream["path"]] == [
            SOURCE_ID,
            MIDDLE_ID,
            TARGET_ID,
        ]

        blast_response = client.get(f"/risk/{SOURCE_ID}/blast-radius")
        assert blast_response.status_code == 200
        blast = blast_response.json()
        assert blast["affected_company_count"] == 2

        companies = {
            item["company_id"]: item
            for item in blast["companies"]
        }
        assert companies[MIDDLE_ID]["hop_distance"] == 1
        assert companies[MIDDLE_ID]["transmission_factor"] == pytest.approx(0.8)
        assert companies[TARGET_ID]["hop_distance"] == 2
        assert companies[TARGET_ID]["transmission_factor"] == pytest.approx(0.28)
