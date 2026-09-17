from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from fastapi.testclient import TestClient

from src.api.app import create_app


EVIDENCE_STATES = {"AVAILABLE", "PARTIAL", "UNAVAILABLE"}


def _check(client: TestClient, method: str, path: str, **kwargs: Any) -> Any:
    response = client.request(method, path, **kwargs)
    if response.status_code != 200:
        raise RuntimeError(
            f"{method} {path} -> {response.status_code}: {response.text}"
        )
    return response.json()


def _expect_status(
    client: TestClient,
    method: str,
    path: str,
    expected: int,
    **kwargs: Any,
) -> Any:
    response = client.request(method, path, **kwargs)
    if response.status_code != expected:
        raise RuntimeError(
            f"{method} {path} expected {expected}, got "
            f"{response.status_code}: {response.text}"
        )
    if response.headers.get("content-type", "").startswith("application/json"):
        return response.json()
    return response.text


def _assert_evidence_state(value: Any, *, context: str) -> None:
    if value not in EVIDENCE_STATES:
        raise RuntimeError(
            f"{context} has invalid/missing evidence state: {value!r}"
        )


def main() -> None:
    report: dict[str, Any] = {}
    app = create_app()

    with TestClient(app) as client:
        report["basic_health"] = _check(client, "GET", "/health")
        report["info"] = _check(client, "GET", "/api/v1/info")

        health = _check(client, "GET", "/api/v1/health/detailed")
        report["health"] = health
        services = health.get("services", {})
        if services.get("neo4j", {}).get("status") != "healthy":
            raise RuntimeError(
                "Neo4j is not healthy; live integration cannot be verified."
            )
        for required_service in (
            "neo4j",
            "agent_llm",
            "websocket",
            "event_poller",
            "event_classifier",
            "news_api",
        ):
            if required_service not in services:
                raise RuntimeError(
                    f"Detailed health is missing service {required_service!r}."
                )

        companies = _check(
            client,
            "GET",
            "/companies",
            params={"limit": 10},
        )
        company_items = companies.get("companies", [])
        if not company_items:
            raise RuntimeError(
                f"No live companies returned by /companies. Response: {companies}"
            )
        company_id = company_items[0].get("company_id")
        if not company_id:
            raise RuntimeError("First company has no canonical company_id.")
        report["company_id"] = company_id

        company = _check(client, "GET", f"/companies/{company_id}")
        report["company"] = company

        network = _check(
            client,
            "GET",
            f"/companies/{company_id}/network",
            params={"depth": 3},
        )
        report["network"] = network
        for relationship in network.get("relationships", []):
            _assert_evidence_state(
                relationship.get("evidence_status"),
                context="network relationship",
            )

        report["risk"] = _check(
            client,
            "GET",
            f"/risk/{company_id}",
            params={"max_hops": 3},
        )

        exposure = _check(
            client,
            "GET",
            f"/risk/{company_id}/exposure",
            params={"max_hops": 3},
        )
        report["exposure"] = exposure
        for item in exposure.get("exposures", []):
            _assert_evidence_state(
                item.get("evidence_status"),
                context="risk exposure",
            )

        history = _check(
            client,
            "GET",
            f"/risk/{company_id}/history",
            params={"max_hops": 3, "limit": 100},
        )
        report["history"] = history
        timestamps = [str(point["timestamp"]) for point in history.get("points", [])]
        if timestamps != sorted(timestamps):
            raise RuntimeError("Risk history points are not chronological.")

        report["blast_radius"] = _check(
            client,
            "GET",
            f"/risk/{company_id}/blast-radius",
            params={"max_hops": 3},
        )

        search = _check(
            client,
            "GET",
            "/api/v1/search",
            params={"q": company.get("name", company_id), "limit": 10},
        )
        report["search"] = search

        events = _check(
            client,
            "GET",
            "/api/v1/events",
            params={"limit": 10, "offset": 0},
        )
        report["events"] = events
        event_items = events.get("events", [])
        if not event_items:
            raise RuntimeError(
                "No persisted live events returned by /api/v1/events. "
                f"Response: {events}"
            )
        event_id = event_items[0].get("event_id")
        if not event_id:
            raise RuntimeError("First event has no canonical event_id.")
        report["event_id"] = event_id

        event = _check(client, "GET", f"/api/v1/events/{event_id}")
        report["event"] = event
        _assert_evidence_state(
            event.get("evidence_status"),
            context="event detail",
        )

        report["event_blast_radius"] = _check(
            client,
            "GET",
            f"/api/v1/events/{event_id}/blast-radius",
            params={"max_hops": 3},
        )

        report["event_validation"] = _check(
            client,
            "POST",
            "/api/v1/events/validate",
            json={
                "event_type": "SUPPLY_DISRUPTION",
                "entity": company_id,
                "severity": "high",
            },
        )

        report["not_found"] = {
            "company": _expect_status(
                client,
                "GET",
                "/companies/__phase0_missing__",
                404,
            ),
            "risk": _expect_status(
                client,
                "GET",
                "/risk/__phase0_missing__",
                404,
            ),
            "event": _expect_status(
                client,
                "GET",
                "/api/v1/events/__phase0_missing__",
                404,
            ),
        }
        report["invalid_depth"] = _expect_status(
            client,
            "GET",
            f"/companies/{company_id}/network",
            422,
            params={"depth": 4},
        )

        try:
            with client.websocket_connect("/risk-stream") as websocket:
                websocket_message = websocket.receive_json()
                if websocket_message.get("type") != "connection.established":
                    raise RuntimeError(
                        "Unexpected WebSocket handshake payload: "
                        f"{websocket_message}"
                    )
                report["websocket"] = websocket_message
        except Exception as exc:
            raise RuntimeError(
                "WebSocket /risk-stream verification failed: "
                f"{type(exc).__name__}: {exc}"
            ) from exc

        llm_status = services.get("agent_llm", {}).get("status")
        if llm_status == "configured":
            agent_response = client.post(
                "/api/v1/agent/query",
                json={
                    "question": (
                        "What supply-chain dependencies are connected to "
                        f"{company.get('name', company_id)}?"
                    )
                },
            )
            report["agent"] = {
                "status_code": agent_response.status_code,
                "body": (
                    agent_response.json()
                    if agent_response.headers.get("content-type", "").startswith(
                        "application/json"
                    )
                    else agent_response.text
                ),
            }
            if agent_response.status_code != 200:
                raise RuntimeError(
                    "POST /api/v1/agent/query -> "
                    f"{agent_response.status_code}: {agent_response.text}"
                )
        else:
            unavailable = _expect_status(
                client,
                "POST",
                "/api/v1/agent/query",
                503,
                json={
                    "question": (
                        "What supply-chain dependencies are connected to "
                        f"{company.get('name', company_id)}?"
                    )
                },
            )
            report["agent"] = {
                "status": "environment-dependent",
                "provider_status": llm_status,
                "unavailable_response": unavailable,
                "real_external_call_tested": False,
            }

    print(json.dumps(report, indent=2, default=str))
    print("\nPHASE 0 LIVE INTEGRATION VERIFICATION PASSED")


if __name__ == "__main__":
    main()
