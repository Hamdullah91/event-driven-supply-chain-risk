from typing import Any

import pytest
from fastapi.testclient import TestClient

from src.api.app import app
from src.api.dependencies import get_event_service


class FakeEventService:
    event = {
        "event_id": "event-001",
        "event_type": "facility_shutdown",
        "source": "news_api",
        "timestamp": "2026-09-16T10:00:00+00:00",
        "entity_id": "tsmc",
        "severity": "high",
        "payload": {
            "article_id": "article-001",
            "title": "TSMC facility disruption",
            "confidence": 0.94,
            "source_url": "https://example.com/article-001",
        },
        "created_at": "2026-09-16T10:01:00+00:00",
    }

    def list_events(self, *, limit: int, offset: int) -> dict[str, Any]:
        return {
            "events": [self.event],
            "count": 1,
            "limit": limit,
            "offset": offset,
        }

    def get_event(self, event_id: str) -> dict[str, Any] | None:
        if event_id != self.event["event_id"]:
            return None
        return self.event


@pytest.fixture
def client() -> TestClient:
    app.dependency_overrides[get_event_service] = lambda: FakeEventService()
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def test_list_events(client: TestClient) -> None:
    response = client.get("/api/v1/events?limit=25&offset=0")
    assert response.status_code == 200
    body = response.json()
    assert body["count"] == 1
    assert body["limit"] == 25
    assert body["offset"] == 0
    assert body["events"][0]["event_id"] == "event-001"
    assert body["events"][0]["severity"] == "high"
    assert body["events"][0]["payload"]["confidence"] == 0.94


def test_get_event(client: TestClient) -> None:
    response = client.get("/api/v1/events/event-001")
    assert response.status_code == 200
    body = response.json()
    assert body["event_type"] == "facility_shutdown"
    assert body["entity_id"] == "tsmc"
    assert body["payload"]["article_id"] == "article-001"


def test_unknown_event_returns_404(client: TestClient) -> None:
    response = client.get("/api/v1/events/missing-event")
    assert response.status_code == 404
    assert response.json()["detail"] == "Event not found"


def test_event_list_pagination_is_validated(client: TestClient) -> None:
    assert client.get("/api/v1/events?limit=0").status_code == 422
    assert client.get("/api/v1/events?limit=501").status_code == 422
    assert client.get("/api/v1/events?offset=-1").status_code == 422


def test_existing_validate_route_is_preserved(client: TestClient) -> None:
    response = client.post(
        "/api/v1/events/validate",
        json={
            "event_type": "SUPPLY_DISRUPTION",
            "entity": "TSMC",
            "severity": 0.8,
        },
    )
    assert response.status_code == 200
    assert response.json()["entity"] == "TSMC"
