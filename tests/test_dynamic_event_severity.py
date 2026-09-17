from __future__ import annotations

from datetime import UTC, datetime

import pytest

from src.api.services.risk import RiskAnalyticsService
from src.events.pipeline import EventPipeline
from src.events.severity import assess_event_severity
from src.events.types import EventSeverity
from src.ingestion.news.classification import ClassifiedNewsArticle
from src.ingestion.news.nlp_processor import NewsNLPResult
from src.nlp.entity_resolution.models import ResolvedEntity


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("A minor outage affected one production line", EventSeverity.LOW),
        ("The supplier reported a temporary closure", EventSeverity.MEDIUM),
        ("The factory shutdown halted production", EventSeverity.HIGH),
        ("The site entered a complete shutdown", EventSeverity.CRITICAL),
        ("The company issued a routine operations update", EventSeverity.UNKNOWN),
    ],
)
def test_rule_based_severity_levels(text: str, expected: EventSeverity) -> None:
    assessment = assess_event_severity(
        event_type="FACILITY_OUTAGE",
        texts=[text],
    )
    assert assessment.severity is expected


def test_classifier_confidence_is_not_used_as_severity() -> None:
    assessment = assess_event_severity(
        event_type="SUPPLY_DISRUPTION",
        texts=["Routine supplier operations update"],
    )
    assert assessment.severity is EventSeverity.UNKNOWN


class FakeGraphRepository:
    def __init__(self) -> None:
        self.saved_event = None

    def save_event(self, event) -> None:
        self.saved_event = event

    def link_event_to_company(self, **kwargs) -> bool:
        return True

    def link_event_to_facility(self, **kwargs) -> bool:
        return True


class FakeRiskRepository:
    def __init__(self, graph_repository: FakeGraphRepository) -> None:
        self.graph_repository = graph_repository

    def get_event_blast_radius(self, event_id: str, *, max_hops: int = 3) -> list[dict]:
        event = self.graph_repository.saved_event
        assert event is not None
        assert str(event.event_id) == event_id
        return [
            {
                "event_id": event_id,
                "event_type": event.event_type.value,
                "severity": event.severity.value,
                "affected_company_id": "tsmc",
                "affected_company_name": "TSMC",
                "target_company_id": "nvidia",
                "target_company_name": "NVIDIA",
                "hop_distance": 1,
                "dependency_weights": [0.8],
                "path_nodes": [
                    {"company_id": "tsmc", "name": "TSMC"},
                    {"company_id": "nvidia", "name": "NVIDIA"},
                ],
            }
        ]


def _classified(title: str) -> ClassifiedNewsArticle:
    now = datetime.now(UTC)
    return ClassifiedNewsArticle(
        article_id="severity-e2e-1",
        title=title,
        url="https://example.com/event",
        source="Example News",
        published_at=now,
        ingested_at=now,
        event_type="FACILITY_OUTAGE",
        confidence=0.91,
        requires_review=False,
        second_event_type="SUPPLY_DISRUPTION",
        second_confidence=0.05,
        confidence_margin=0.86,
    )


def _nlp() -> NewsNLPResult:
    return NewsNLPResult(
        article_id="severity-e2e-1",
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


def test_dynamic_event_severity_produces_nonzero_propagated_risk() -> None:
    graph_repository = FakeGraphRepository()
    pipeline = EventPipeline(graph_repository=graph_repository)

    result = pipeline.process(
        classified=_classified("TSMC factory shutdown halted production"),
        nlp_result=_nlp(),
    )

    assert result.event.severity is EventSeverity.HIGH
    assert result.event.payload["confidence"] == pytest.approx(0.91)
    assert result.event.payload["severity_cue"] in {
        "halted production",
        "factory shutdown",
    }
    assert "severity_reason" in result.event.payload

    risk_service = RiskAnalyticsService(FakeRiskRepository(graph_repository))
    blast = risk_service.get_event_blast_radius(str(result.event.event_id))
    propagated = blast["companies"][0]

    assert propagated["initial_risk"] == pytest.approx(0.75)
    assert propagated["path_dependency"] == pytest.approx(0.8)
    assert propagated["distance_decay"] == pytest.approx(1.0)
    assert propagated["propagated_risk"] == pytest.approx(0.6)
