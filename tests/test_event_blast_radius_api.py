from typing import Any

import pytest
from fastapi.testclient import TestClient

from src.api.app import app
from src.api.dependencies import get_risk_service


class FakeEventRiskService:
    def event_exists(self, event_id: str) -> bool:
        return event_id == "event-1"

    def get_event_blast_radius(self, event_id: str, *, max_hops: int) -> dict[str, Any]:
        return {
            "event_id": event_id,
            "event_type": "supply_disruption",
            "severity": "high",
            "max_hops": max_hops,
            "affected_company_count": 2,
            "hop_counts": {"0": 1, "1": 1, "2": 0, "3": 0},
            "companies": [
                {
                    "company_id": "tsmc",
                    "company_name": "TSMC",
                    "origin_company_id": "tsmc",
                    "origin_company_name": "TSMC",
                    "hop_distance": 0,
                    "initial_risk": 0.75,
                    "path_dependency": 1.0,
                    "distance_decay": 1.0,
                    "propagated_risk": 0.75,
                    "path": [{"company_id": "tsmc", "name": "TSMC"}],
                },
                {
                    "company_id": "nvidia",
                    "company_name": "NVIDIA",
                    "origin_company_id": "tsmc",
                    "origin_company_name": "TSMC",
                    "hop_distance": 1,
                    "initial_risk": 0.75,
                    "path_dependency": 0.8,
                    "distance_decay": 1.0,
                    "propagated_risk": 0.6,
                    "path": [
                        {"company_id": "tsmc", "name": "TSMC"},
                        {"company_id": "nvidia", "name": "NVIDIA"},
                    ],
                },
            ],
        }


@pytest.fixture
def client() -> TestClient:
    app.dependency_overrides[get_risk_service] = lambda: FakeEventRiskService()
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def test_get_event_blast_radius(client: TestClient) -> None:
    response = client.get("/api/v1/events/event-1/blast-radius?max_hops=3")
    assert response.status_code == 200
    body = response.json()
    assert body["event_id"] == "event-1"
    assert body["affected_company_count"] == 2
    assert body["hop_counts"]["0"] == 1
    assert body["companies"][0]["hop_distance"] == 0
    assert body["companies"][1]["propagated_risk"] == pytest.approx(0.6)


def test_unknown_event_returns_404(client: TestClient) -> None:
    response = client.get("/api/v1/events/unknown/blast-radius")
    assert response.status_code == 404


def test_event_blast_radius_hops_are_bounded(client: TestClient) -> None:
    assert client.get("/api/v1/events/event-1/blast-radius?max_hops=0").status_code == 422
    assert client.get("/api/v1/events/event-1/blast-radius?max_hops=4").status_code == 422
