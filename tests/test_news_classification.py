from datetime import UTC, datetime

from src.ingestion.news.classification import (
    NewsClassificationService,
)
from src.ingestion.news.models import NewsArticle
from src.ml.event_classifier import ClassificationResult


class FakeEventClassifier:
    def classify(
        self,
        article: str,
    ) -> ClassificationResult:
        assert "Fire shuts down semiconductor plant" in article
        assert "Production was suspended" in article
        assert "Engineers are assessing damage" in article

        return ClassificationResult(
            event_type="FACILITY_OUTAGE",
            confidence=0.94,
            requires_review=False,
            second_event_type="SUPPLY_DISRUPTION",
            second_confidence=0.04,
            confidence_margin=0.90,
        )


def build_test_article() -> NewsArticle:
    return NewsArticle(
        article_id="a" * 64,
        title="Fire shuts down semiconductor plant",
        description="Production was suspended after a major fire.",
        content="Engineers are assessing damage at the facility.",
        url="https://example.com/article",
        source="Test News",
        published_at=datetime(
            2026,
            9,
            8,
            7,
            30,
            tzinfo=UTC,
        ),
        ingested_at=datetime(
            2026,
            9,
            8,
            7,
            35,
            tzinfo=UTC,
        ),
    )


def test_build_article_text_combines_fields() -> None:
    article = build_test_article()

    text = NewsClassificationService.build_article_text(
        article
    )

    assert article.title in text
    assert article.description in text
    assert article.content in text


def test_classify_news_article() -> None:
    article = build_test_article()

    service = NewsClassificationService(
        classifier=FakeEventClassifier(),  # type: ignore[arg-type]
    )

    result = service.classify(article)

    assert result.article_id == article.article_id
    assert result.title == article.title
    assert result.url == article.url
    assert result.source == article.source

    assert result.event_type == "FACILITY_OUTAGE"
    assert result.confidence == 0.94
    assert result.requires_review is False

    assert result.second_event_type == "SUPPLY_DISRUPTION"
    assert result.second_confidence == 0.04
    assert result.confidence_margin == 0.90


def test_classification_preserves_timestamps() -> None:
    article = build_test_article()

    service = NewsClassificationService(
        classifier=FakeEventClassifier(),  # type: ignore[arg-type]
    )

    result = service.classify(article)

    assert result.published_at == article.published_at
    assert result.ingested_at == article.ingested_at