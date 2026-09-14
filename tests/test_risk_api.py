from typing import Any

import pytest
from fastapi.testclient import TestClient

from src.api.app import app
from src.api.dependencies import get_risk_service
from src.api.services.risk import RiskAnalyticsService


class FakeRiskRepository:
    def company_exists(self, company_id: str) -> bool:
        return company_id in {"tsmc", "tesla"}

    def get_company_blast_radius(
        self,
        company_id: str,
        *,
        max_hops: int,
    ) -> list[dict[str, Any]]:
        return [
            {
                "source_company_id": company_id,
                "source_company_name": "TSMC",
                "target_company_id": "nvidia",
                "target_company_name": "NVIDIA",
                "hop_distance": 1,
                "path_nodes": [
                    {"company_id": company_id, "name": "TSMC"},
                    {"company_id": "nvidia", "name": "NVIDIA"},
                ],
                "path_relationships": [
                    {"dependency_weight": 0.8, "weight_source": "relationship"}
                ],
            }
        ]

    def get_company_event_exposure(
        self,
        company_id: str,
        *,
        max_hops: int,
    ) -> list[dict[str, Any]]:
        if company_id != "tsmc":
            return []
        return [
            {
                "event_id": "evt-direct",
                "event_type": "FACILITY_OUTAGE",
                "severity": "high",
                "timestamp": "2026-09-14T08:00:00Z",
                "source": "test",
                "confidence": 0.95,
                "description": "Direct outage",
                "affected_company_id": "tsmc",
                "affected_company_name": "TSMC",
                "target_company_id": "tsmc",
                "target_company_name": "TSMC",
                "hop_distance": 0,
                "dependency_weights": [],
                "path_nodes": [{"company_id": "tsmc", "name": "TSMC"}],
            },
            {
                "event_id": "evt-upstream",
                "event_type": "SUPPLY_DISRUPTION",
                "severity": "medium",
                "timestamp": "2026-09-14T07:00:00Z",
                "source": "test",
                "confidence": 0.90,
                "description": "Upstream disruption",
                "affected_company_id": "supplier-a",
                "affected_company_name": "Supplier A",
                "target_company_id": "tsmc",
                "target_company_name": "TSMC",
                "hop_distance": 1,
                "dependency_weights": [0.5],
                "path_nodes": [
                    {"company_id": "supplier-a", "name": "Supplier A"},
                    {"company_id": "tsmc", "name": "TSMC"},
                ],
            },
            {
                "event_id": "evt-upstream",
                "event_type": "SUPPLY_DISRUPTION",
                "severity": "medium",
                "timestamp": "2026-09-14T07:00:00Z",
                "source": "test",
                "confidence": 0.90,
                "description": "Weaker alternate path",
                "affected_company_id": "supplier-a",
                "affected_company_name": "Supplier A",
                "target_company_id": "tsmc",
                "target_company_name": "TSMC",
                "hop_distance": 2,
                "dependency_weights": [0.5, 0.5],
                "path_nodes": [
                    {"company_id": "supplier-a", "name": "Supplier A"},
                    {"company_id": "supplier-b", "name": "Supplier B"},
                    {"company_id": "tsmc", "name": "TSMC"},
                ],
            },
        ]


@pytest.fixture
def risk_service() -> RiskAnalyticsService:
    return RiskAnalyticsService(FakeRiskRepository())


@pytest.fixture
def client(risk_service: RiskAnalyticsService) -> TestClient:
    app.dependency_overrides[get_risk_service] = lambda: risk_service
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def test_direct_zero_hop_exposure(risk_service: RiskAnalyticsService) -> None:
    result = risk_service.get_exposure("tsmc")
    direct = next(
        item for item in result["exposures"] if item["event_id"] == "evt-direct"
    )
    assert direct["hop_distance"] == 0
    assert direct["propagated_risk"] == pytest.approx(0.75)
    assert direct["distance_decay"] == pytest.approx(1.0)


def test_same_event_multiple_paths_is_aggregated_once(
    risk_service: RiskAnalyticsService,
) -> None:
    result = risk_service.get_company_risk("tsmc")
    assert result["risk_score"] == pytest.approx(0.8125)
    assert result["contributing_event_count"] == 2
    assert result["risk_level"] == "CRITICAL"


def test_blast_radius_returns_structural_transmission(
    risk_service: RiskAnalyticsService,
) -> None:
    result = risk_service.get_blast_radius("tsmc")
    assert result["affected_company_count"] == 1
    assert result["companies"][0]["company_id"] == "nvidia"
    assert result["companies"][0]["transmission_factor"] == pytest.approx(0.8)


def test_risk_endpoints(client: TestClient) -> None:
    assert client.get("/risk/tsmc").status_code == 200
    assert client.get("/risk/tsmc/blast-radius?max_hops=3").status_code == 200
    assert client.get("/risk/tsmc/exposure?max_hops=3").status_code == 200


def test_unknown_company_returns_404(client: TestClient) -> None:
    assert client.get("/risk/unknown").status_code == 404
    assert client.get("/risk/unknown/blast-radius").status_code == 404
    assert client.get("/risk/unknown/exposure").status_code == 404


def test_max_hops_is_bounded(client: TestClient) -> None:
    assert client.get("/risk/tsmc?max_hops=0").status_code == 422
    assert client.get("/risk/tsmc?max_hops=4").status_code == 422
    assert client.get("/risk/tsmc/blast-radius?max_hops=4").status_code == 422
    assert client.get("/risk/tsmc/exposure?max_hops=0").status_code == 422


def test_no_exposure_returns_zero_risk(client: TestClient) -> None:
    response = client.get("/risk/tesla")
    assert response.status_code == 200
    assert response.json()["risk_score"] == 0.0
    assert response.json()["risk_level"] == "NONE"
    assert response.json()["contributing_event_count"] == 0
