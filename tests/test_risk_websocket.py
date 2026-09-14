from __future__ import annotations

import asyncio
from typing import Any

from fastapi.testclient import TestClient

from src.api.app import app
from src.api.services.risk_stream import RiskStreamService
from src.api.websocket import ConnectionManager


class FakeWebSocket:
    def __init__(self, *, fail: bool = False) -> None:
        self.fail = fail
        self.accepted = False
        self.messages: list[dict[str, Any]] = []

    async def accept(self) -> None:
        self.accepted = True

    async def send_json(self, message: dict[str, Any]) -> None:
        if self.fail:
            raise RuntimeError("WebSocket disconnected.")
        self.messages.append(message)


class FakeRiskService:
    def get_company_risk(
        self,
        company_id: str,
        *,
        max_hops: int = 3,
    ) -> dict:
        return {
            "company_id": company_id,
            "risk_score": 0.72,
            "risk_level": "HIGH",
            "contributing_event_count": 2,
            "max_hops": max_hops,
        }


def test_risk_stream_connection() -> None:
    with TestClient(app) as client:
        with client.websocket_connect("/risk-stream") as websocket:
            message = websocket.receive_json()
            assert message["type"] == "connection.established"
            assert "risk stream" in message["message"].lower()


def test_connection_manager_broadcasts_to_multiple_clients() -> None:
    manager = ConnectionManager()
    first = FakeWebSocket()
    second = FakeWebSocket()

    async def scenario() -> None:
        await manager.connect(first)
        await manager.connect(second)
        await manager.broadcast(
            {
                "type": "risk.updated",
                "company_id": "tsmc",
            }
        )

    asyncio.run(scenario())

    assert first.accepted is True
    assert second.accepted is True
    assert first.messages[0]["company_id"] == "tsmc"
    assert second.messages[0]["company_id"] == "tsmc"


def test_failed_client_is_removed_without_breaking_broadcast() -> None:
    manager = ConnectionManager()
    healthy = FakeWebSocket()
    failed = FakeWebSocket(fail=True)

    async def scenario() -> None:
        await manager.connect(healthy)
        await manager.connect(failed)
        await manager.broadcast(
            {
                "type": "risk.updated",
                "company_id": "nvidia",
            }
        )

    asyncio.run(scenario())

    assert healthy in manager.active_connections
    assert failed not in manager.active_connections
    assert healthy.messages[0]["company_id"] == "nvidia"


def test_risk_stream_service_publishes_graph_grounded_risk() -> None:
    manager = ConnectionManager()
    websocket = FakeWebSocket()

    async def scenario() -> dict:
        await manager.connect(websocket)
        service = RiskStreamService(
            FakeRiskService(),
            manager=manager,
        )
        return await service.publish_company_risk(
            company_id="nvidia",
            event_id="evt-day48",
            event_type="FACILITY_OUTAGE",
        )

    message = asyncio.run(scenario())

    assert message["type"] == "risk.updated"
    assert message["company_id"] == "nvidia"
    assert message["risk_score"] == 0.72
    assert message["risk_level"] == "HIGH"
    assert message["event_id"] == "evt-day48"
    assert message["trigger_event_type"] == "FACILITY_OUTAGE"
    assert websocket.messages == [message]
