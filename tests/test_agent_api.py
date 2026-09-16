from __future__ import annotations

from fastapi.testclient import TestClient

from src.agent.evidence import EvidenceStatus
from src.agent.explainer import GroundedExplanation
from src.api.app import app
from src.api.dependencies import get_agent_service


class FakeAgentService:
    async def answer(self, question: str) -> GroundedExplanation:
        assert question == "How is NVIDIA exposed to TSMC?"
        return GroundedExplanation(
            answer="The graph identifies the direct dependency path TSMC → NVIDIA.",
            evidence_status=EvidenceStatus.SUFFICIENT,
            affected_entities=["TSMC"],
            dependency_paths=[["TSMC", "NVIDIA"]],
            hop_counts=[1],
            event_refs=["event:1"],
            path_ids=["P1"],
            warnings=[],
        )


class RejectingAgentService:
    async def answer(self, question: str) -> GroundedExplanation:
        raise ValueError("This question does not produce a graph query.")


def test_agent_query_returns_grounded_explanation() -> None:
    app.dependency_overrides[get_agent_service] = lambda: FakeAgentService()
    try:
        with TestClient(app) as client:
            response = client.post(
                "/api/v1/agent/query",
                json={"question": "How is NVIDIA exposed to TSMC?"},
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    body = response.json()
    assert body["evidence_status"] == "SUFFICIENT"
    assert body["dependency_paths"] == [["TSMC", "NVIDIA"]]
    assert body["hop_counts"] == [1]
    assert body["event_refs"] == ["event:1"]
    assert body["path_ids"] == ["P1"]


def test_agent_query_rejects_blank_question() -> None:
    app.dependency_overrides[get_agent_service] = lambda: FakeAgentService()
    try:
        with TestClient(app) as client:
            response = client.post(
                "/api/v1/agent/query",
                json={"question": ""},
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 422


def test_agent_query_maps_unsupported_route_to_422() -> None:
    app.dependency_overrides[get_agent_service] = lambda: RejectingAgentService()
    try:
        with TestClient(app) as client:
            response = client.post(
                "/api/v1/agent/query",
                json={"question": "Give me a general summary."},
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 422
    assert "graph query" in response.json()["detail"]


def test_agent_query_is_unavailable_until_provider_is_configured() -> None:
    with TestClient(app) as client:
        response = client.post(
            "/api/v1/agent/query",
            json={"question": "How is NVIDIA exposed to TSMC?"},
        )

    assert response.status_code == 503
    detail = response.json()["detail"]
    assert "Agentic RAG provider is not configured" in detail
    assert "LLM_PROVIDER=openai" in detail
