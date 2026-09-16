from __future__ import annotations

import asyncio
from dataclasses import dataclass
from types import SimpleNamespace

from src.ingestion.news.poller import NewsPoller


@dataclass
class FakeArticle:
    article_id: str = "article-a5"
    source: str = "test-news"
    title: str = "Supplier disruption"


class FakeClient:
    async def fetch_articles(self, **kwargs):
        return [FakeArticle()]


class FakeRepository:
    def save(self, article) -> bool:
        return True


class FakeNLPProcessor:
    def process(self, article):
        return SimpleNamespace(article_id=article.article_id)


class FakeClassificationService:
    def classify(self, article):
        return SimpleNamespace(
            article_id=article.article_id,
            event_type="SUPPLY_DISRUPTION",
            confidence=0.95,
            requires_review=False,
        )


class FakeEventPipeline:
    def process(self, *, classified, nlp_result):
        event = SimpleNamespace(
            event_id="event-a5",
            event_type=SimpleNamespace(value="supply_disruption"),
        )
        return SimpleNamespace(
            event=event,
            linked_companies=2,
            failed_company_links=0,
            linked_company_ids=("tsmc", "nvidia"),
        )


class FakeRiskStreamService:
    def __init__(self) -> None:
        self.calls = []

    async def publish_company_risk(self, **kwargs):
        self.calls.append(kwargs)
        return {"type": "risk.updated", **kwargs}


def test_new_event_automatically_publishes_risk_for_linked_companies() -> None:
    stream = FakeRiskStreamService()
    poller = NewsPoller(
        client=FakeClient(),
        repository=FakeRepository(),
        query="supply chain",
        nlp_processor=FakeNLPProcessor(),
        classification_service=FakeClassificationService(),
        event_pipeline=FakeEventPipeline(),
        risk_stream_service=stream,
    )

    asyncio.run(poller.poll_once())

    assert [call["company_id"] for call in stream.calls] == ["tsmc", "nvidia"]
    assert all(call["event_id"] == "event-a5" for call in stream.calls)
    assert all(call["event_type"] == "supply_disruption" for call in stream.calls)


def test_stream_failure_does_not_fail_persisted_event() -> None:
    class FailingStream(FakeRiskStreamService):
        async def publish_company_risk(self, **kwargs):
            raise RuntimeError("stream unavailable")

    poller = NewsPoller(
        client=FakeClient(),
        repository=FakeRepository(),
        query="supply chain",
        nlp_processor=FakeNLPProcessor(),
        classification_service=FakeClassificationService(),
        event_pipeline=FakeEventPipeline(),
        risk_stream_service=FailingStream(),
    )

    asyncio.run(poller.poll_once())
