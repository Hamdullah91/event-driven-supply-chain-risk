from __future__ import annotations

from datetime import UTC, datetime

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.api.routes.websocket import router as websocket_router
from src.api.services.risk import RiskAnalyticsService
from src.api.services.risk_stream import RiskStreamService
from src.events.pipeline import EventPipeline
from src.ingestion.news.classification import ClassifiedNewsArticle
from src.ingestion.news.nlp_processor import NewsNLPResult
from src.ingestion.news.poller import NewsPoller
from src.nlp.entity_resolution.models import ResolvedEntity


COMPANY_PATH = (
    {"company_id": "tsmc", "company_name": "TSMC"},
    {"company_id": "nvidia", "company_name": "NVIDIA"},
    {"company_id": "amd", "company_name": "AMD"},
    {"company_id": "dell", "company_name": "Dell"},
)
DEPENDENCY_WEIGHTS = (0.9, 0.8, 0.6)


class InMemoryGraphRepository:
    def __init__(self) -> None:
        self.event = None
        self.linked_company_ids: list[str] = []

    def save_event(self, event) -> None:
        self.event = event

    def link_event_to_company(self, **kwargs) -> bool:
        company_id = str(kwargs["company_id"])
        if company_id not in self.linked_company_ids:
            self.linked_company_ids.append(company_id)
        return True

    def link_event_to_facility(self, **kwargs) -> bool:
        return True


class EventBackedRiskRepository:
    """Deterministic graph rows for the full direct-to-three-hop event path."""

    def __init__(self, graph_repository: InMemoryGraphRepository) -> None:
        self.graph_repository = graph_repository

    def _event_rows(self, event_id: str, *, max_hops: int) -> list[dict]:
        event = self.graph_repository.event
        assert event is not None
        assert str(event.event_id) == event_id

        if "tsmc" not in self.graph_repository.linked_company_ids:
            return []

        rows: list[dict] = []
        for hop_distance, target in enumerate(COMPANY_PATH[: max_hops + 1]):
            rows.append(
                {
                    "event_id": str(event.event_id),
                    "event_type": event.event_type.value,
                    "severity": event.severity.value,
                    "affected_company_id": "tsmc",
                    "affected_company_name": "TSMC",
                    "target_company_id": target["company_id"],
                    "target_company_name": target["company_name"],
                    "hop_distance": hop_distance,
                    "dependency_weights": list(DEPENDENCY_WEIGHTS[:hop_distance]),
                    "path_nodes": [
                        {
                            "company_id": node["company_id"],
                            "name": node["company_name"],
                        }
                        for node in COMPANY_PATH[: hop_distance + 1]
                    ],
                }
            )
        return rows

    def get_event_blast_radius(self, event_id: str, *, max_hops: int = 3) -> list[dict]:
        return self._event_rows(event_id, max_hops=max_hops)

    def get_company_event_exposure(self, company_id: str, *, max_hops: int = 3) -> list[dict]:
        event = self.graph_repository.event
        assert event is not None
        return [
            row
            for row in self._event_rows(str(event.event_id), max_hops=max_hops)
            if row["target_company_id"] == company_id
        ]


def _classification() -> ClassifiedNewsArticle:
    now = datetime.now(UTC)
    return ClassifiedNewsArticle(
        article_id="ws-runtime-event-1",
        title="TSMC factory shutdown halted production",
        url="https://example.com/ws-runtime-event",
        source="Runtime Test News",
        published_at=now,
        ingested_at=now,
        event_type="FACILITY_OUTAGE",
        confidence=0.93,
        requires_review=False,
        second_event_type="SUPPLY_DISRUPTION",
        second_confidence=0.04,
        confidence_margin=0.89,
    )


def _nlp() -> NewsNLPResult:
    return NewsNLPResult(
        article_id="ws-runtime-event-1",
        entities=[],
        resolved_companies=[
            ResolvedEntity(
                original_name="TSMC",
                normalized_name="tsmc",
                canonical_id="tsmc",
                canonical_name="TSMC",
                confidence=1.0,
                resolution_method="alias_exact",
            )
        ],
        triplets=[],
    )


def test_processed_event_reaches_connected_client_for_direct_and_downstream_companies() -> None:
    graph_repository = InMemoryGraphRepository()
    event_pipeline = EventPipeline(graph_repository=graph_repository)
    risk_service = RiskAnalyticsService(EventBackedRiskRepository(graph_repository))
    risk_stream = RiskStreamService(risk_service)

    # The EventPipeline, RiskAnalyticsService, RiskStreamService, NewsPoller
    # publication method, ConnectionManager, and WebSocket route are real.
    # Only the graph repository is deterministic so every hop can be tested
    # without depending on an external NewsAPI response or live Neo4j.
    poller = object.__new__(NewsPoller)
    poller.risk_stream_service = risk_stream

    test_app = FastAPI()
    test_app.include_router(websocket_router)

    @test_app.post("/test/process-event")
    async def process_event() -> dict:
        result = event_pipeline.process(
            classified=_classification(),
            nlp_result=_nlp(),
        )
        await poller._publish_event_risk(result)
        return {
            "event_id": str(result.event.event_id),
            "severity": result.event.severity.value,
        }

    with TestClient(test_app) as client:
        with client.websocket_connect("/risk-stream") as websocket:
            handshake = websocket.receive_json()
            assert handshake["type"] == "connection.established"

            response = client.post("/test/process-event")
            assert response.status_code == 200
            assert response.json()["severity"] == "high"

            updates = [websocket.receive_json() for _ in COMPANY_PATH]

    event_id = response.json()["event_id"]
    updates_by_company = {message["company_id"]: message for message in updates}

    assert set(updates_by_company) == {"tsmc", "nvidia", "amd", "dell"}
    assert len(updates) == len(updates_by_company) == 4
    assert "unrelated-company" not in updates_by_company

    expected_risk = {
        "tsmc": (0.75, "CRITICAL"),
        "nvidia": (0.675, "HIGH"),
        "amd": (0.378, "MEDIUM"),
        "dell": (0.15876, "LOW"),
    }
    for company_id, (risk_score, risk_level) in expected_risk.items():
        message = updates_by_company[company_id]
        assert message["type"] == "risk.updated"
        assert message["event_id"] == event_id
        assert message["company_id"] == company_id
        assert message["risk_score"] == pytest.approx(risk_score)
        assert message["risk_level"] == risk_level
        assert message["contributing_event_count"] == 1
        assert message["max_hops"] == 3
        assert message["trigger_event_type"] == "facility_outage"
