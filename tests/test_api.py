from fastapi.testclient import TestClient

from src.api.app import app


client = TestClient(app)


def test_health_check() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_info_endpoint() -> None:
    response = client.get("/api/v1/info")
    assert response.status_code == 200
    body = response.json()
    assert "app_name" in body
    assert body["environment"] == "development"


def test_valid_event_is_accepted() -> None:
    payload = {
        "event_type": "FACILITY_OUTAGE",
        "entity": "TSMC",
        "severity": "high",
    }
    response = client.post("/api/v1/events/validate", json=payload)
    assert response.status_code == 200
    assert response.json() == payload


def test_unknown_event_type_is_rejected() -> None:
    payload = {
        "event_type": "ALIEN_ATTACK",
        "entity": "TSMC",
        "severity": "high",
    }
    response = client.post("/api/v1/events/validate", json=payload)
    assert response.status_code == 422


def test_numeric_severity_is_rejected() -> None:
    payload = {
        "event_type": "FACILITY_OUTAGE",
        "entity": "TSMC",
        "severity": 0.85,
    }
    response = client.post("/api/v1/events/validate", json=payload)
    assert response.status_code == 422


def test_unknown_severity_label_is_rejected() -> None:
    payload = {
        "event_type": "FACILITY_OUTAGE",
        "entity": "TSMC",
        "severity": "extreme",
    }
    response = client.post("/api/v1/events/validate", json=payload)
    assert response.status_code == 422


def test_empty_entity_is_rejected() -> None:
    payload = {
        "event_type": "FACILITY_OUTAGE",
        "entity": "",
        "severity": "high",
    }
    response = client.post("/api/v1/events/validate", json=payload)
    assert response.status_code == 422
