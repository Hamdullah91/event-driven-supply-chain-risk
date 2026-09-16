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


def _check(client: TestClient, method: str, path: str, **kwargs: Any) -> Any:
    response = client.request(method, path, **kwargs)
    if response.status_code != 200:
        raise RuntimeError(f"{method} {path} -> {response.status_code}: {response.text}")
    return response.json()


def main() -> None:
    report: dict[str, Any] = {}
    app = create_app()
    with TestClient(app) as client:
        health = _check(client, "GET", "/api/v1/health/detailed")
        report["health"] = health
        if health.get("services", {}).get("neo4j", {}).get("status") != "healthy":
            raise RuntimeError("Neo4j is not healthy; live integration cannot be verified.")

        companies = _check(client, "GET", "/companies", params={"limit": 10})
        company_items = companies.get("companies", [])
        if not company_items:
            raise RuntimeError(f"No live companies returned by /companies. Response: {companies}")
        company_id = company_items[0].get("company_id")
        if not company_id:
            raise RuntimeError("First company has no canonical company_id.")
        report["company_id"] = company_id

        report["company"] = _check(client, "GET", f"/companies/{company_id}")
        report["network"] = _check(client, "GET", f"/companies/{company_id}/network", params={"depth": 3})
        report["risk"] = _check(client, "GET", f"/risk/{company_id}", params={"max_hops": 3})
        report["exposure"] = _check(client, "GET", f"/risk/{company_id}/exposure", params={"max_hops": 3})
        report["history"] = _check(client, "GET", f"/risk/{company_id}/history", params={"max_hops": 3, "limit": 100})
        report["blast_radius"] = _check(client, "GET", f"/risk/{company_id}/blast-radius", params={"max_hops": 3})

        search = _check(client, "GET", "/api/v1/search", params={"q": report["company"].get("name", company_id), "limit": 10})
        report["search"] = search

        events = _check(client, "GET", "/api/v1/events", params={"limit": 10, "offset": 0})
        report["events"] = events
        event_items = events.get("events", [])
        if not event_items:
            raise RuntimeError(f"No persisted live events returned by /api/v1/events. Response: {events}")
        event_id = event_items[0].get("event_id")
        if not event_id:
            raise RuntimeError("First event has no canonical event_id.")
        report["event_id"] = event_id
        report["event"] = _check(client, "GET", f"/api/v1/events/{event_id}")
        report["event_blast_radius"] = _check(client, "GET", f"/api/v1/events/{event_id}/blast-radius", params={"max_hops": 3})

        try:
            with client.websocket_connect("/risk-stream") as websocket:
                report["websocket"] = websocket.receive_json()
        except Exception as exc:
            raise RuntimeError(f"WebSocket /risk-stream verification failed: {type(exc).__name__}: {exc}") from exc

        llm_status = health.get("services", {}).get("agent_llm", {}).get("status")
        if llm_status == "configured":
            agent_response = client.post(
                "/api/v1/agent/query",
                json={"question": f"What supply-chain dependencies are connected to {report['company'].get('name', company_id)}?"},
            )
            report["agent"] = {
                "status_code": agent_response.status_code,
                "body": agent_response.json() if agent_response.headers.get("content-type", "").startswith("application/json") else agent_response.text,
            }
            if agent_response.status_code != 200:
                raise RuntimeError(f"POST /api/v1/agent/query -> {agent_response.status_code}: {agent_response.text}")
        else:
            report["agent"] = {"status": "unverified", "reason": "Agent LLM is not configured in this runtime."}

    print(json.dumps(report, indent=2, default=str))
    print("\nC6 LIVE INTEGRATION VERIFICATION PASSED")


if __name__ == "__main__":
    main()
