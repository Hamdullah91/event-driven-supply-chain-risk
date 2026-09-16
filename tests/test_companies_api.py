from typing import Any

import pytest
from fastapi.testclient import TestClient

from src.api.app import app
from src.api.dependencies import get_company_service


class FakeCompanyService:
    def list_companies(
        self,
        *,
        limit: int,
        offset: int,
        search: str | None = None,
        industry_id: str | None = None,
        entity_type: str | None = None,
    ) -> dict[str, Any]:
        return {
            "companies": [
                {
                    "company_id": "tsmc",
                    "name": "TSMC",
                    "legal_name": "Taiwan Semiconductor Manufacturing Company Limited",
                    "entity_type": "core",
                    "industry_id": "semiconductors",
                }
            ],
            "count": 1,
            "limit": limit,
            "offset": offset,
        }

    def get_company(self, company_id: str) -> dict[str, Any] | None:
        if company_id != "tsmc":
            return None
        return {
            "company_id": "tsmc",
            "name": "TSMC",
            "legal_name": "Taiwan Semiconductor Manufacturing Company Limited",
            "entity_type": "core",
            "industry_id": "semiconductors",
            "seed_source": "manual_baseline",
            "facilities": ["Fab 18"],
            "products": ["Advanced Logic Chips"],
            "materials": [],
            "technologies": ["EUV Lithography"],
        }

    def get_company_network(self, company_id: str, *, depth: int) -> dict[str, Any] | None:
        if company_id != "tsmc":
            return None
        return {
            "company_id": company_id,
            "depth": depth,
            "nodes": [
                {"id": "company:tsmc", "label": "Company", "name": "TSMC", "properties": {"company_id": "tsmc", "name": "TSMC"}},
                {"id": "company:nvidia", "label": "Company", "name": "NVIDIA", "properties": {"company_id": "nvidia", "name": "NVIDIA"}},
            ],
            "relationships": [
                {"id": "rel-1", "source": "company:tsmc", "target": "company:nvidia", "relationship_type": "SUPPLIES", "properties": {"confidence": 1.0}}
            ],
        }


@pytest.fixture
def client() -> TestClient:
    app.dependency_overrides[get_company_service] = lambda: FakeCompanyService()
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def test_list_companies(client: TestClient) -> None:
    response = client.get("/companies?limit=10&offset=0")
    assert response.status_code == 200
    body = response.json()
    assert body["count"] == 1
    assert body["limit"] == 10
    assert body["companies"][0]["company_id"] == "tsmc"


def test_get_company(client: TestClient) -> None:
    response = client.get("/companies/tsmc")
    assert response.status_code == 200
    assert response.json()["technologies"] == ["EUV Lithography"]


def test_unknown_company_returns_404(client: TestClient) -> None:
    response = client.get("/companies/unknown")
    assert response.status_code == 404


def test_company_network(client: TestClient) -> None:
    response = client.get("/companies/tsmc/network?depth=2")
    assert response.status_code == 200
    body = response.json()
    assert body["depth"] == 2
    assert len(body["nodes"]) == 2
    assert body["relationships"][0]["relationship_type"] == "SUPPLIES"


def test_network_depth_is_bounded(client: TestClient) -> None:
    assert client.get("/companies/tsmc/network?depth=0").status_code == 422
    assert client.get("/companies/tsmc/network?depth=4").status_code == 422


def test_list_pagination_is_validated(client: TestClient) -> None:
    assert client.get("/companies?limit=0").status_code == 422
    assert client.get("/companies?offset=-1").status_code == 422
