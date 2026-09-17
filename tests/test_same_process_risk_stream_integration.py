from __future__ import annotations

from datetime import UTC, datetime

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


class InMemoryGraphRepository:
    def __init__(self) -> None:
        self.event = None

    def save_event(self, event) -> None:
        self.event = event

    def link_event_to_company(self, **kwargs) -> bool:
        return True

    def link_event_to_facility(self, **kwargs) -> bool:
        return True


class EventBackedRiskRepository:
    def __init__(self, graph_repository: InMemoryGraphRepository) -> None:
        self.graph_repository = graph_repository

    def get_company_event_exposure(self, company_id: str, *, max_hops: int = 3) -> list[dict]:
        event = self.graph_repository.event
        assert event is not None
        return [
            {
                "event_id": str(event.event_id),
                "event_type": event.event_type.value,
                "severity": event.severity.value,
                "timestamp": event.timestamp,
                "source": event.source,
                "confidence": event.payload.get("confidence"),
                "description": event.payload.get("title"),
                "affected_company_id": company_id,
                "affected_company_name": "TSMC",
                "target_company_id": company_id,
                "target_company_name": "TSMC",
                "hop_distance": 0,
                "dependency_weights": [],
                "path_nodes": [{"company_id": company_id, "name": "TSMC"}],
            }
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


def test_processed_event_reaches_connected_risk_stream_client() -> None:
    graph_repository = InMemoryGraphRepository()
    event_pipeline = EventPipeline(graph_repository=graph_repository)
    risk_service = RiskAnalyticsService(EventBackedRiskRepository(graph_repository))
    risk_stream = RiskStreamService(risk_service)

    # _publish_event_risk only needs the configured stream service. Keeping the
    # real method in the test verifies the NewsPoller event->stream wiring without
    # calling an external news provider.
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

            update = websocket.receive_json()

    assert update["type"] == "risk.updated"
    assert update["event_id"] == response.json()["event_id"]
    assert update["company_id"] == "tsmc"
    assert update["risk_score"] == 0.75
    assert update["risk_level"] == "CRITICAL"  # threshold is >= 0.75
    assert update["contributing_event_count"] == 1
    assert update["trigger_event_type"] == "facility_outage"
