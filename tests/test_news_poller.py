from __future__ import annotations

from datetime import UTC, datetime

from src.ingestion.news.models import (
    NewsArticle,
    build_article_id,
    normalize_url,
)
from src.ingestion.news.repository import NewsRepository


def test_normalize_url_removes_tracking_parameters() -> None:
    url = (
        "https://example.com/article"
        "?utm_source=test&id=42"
    )

    result = normalize_url(url)

    assert "utm_source" not in result
    assert "id=42" in result


def test_same_url_generates_same_article_id() -> None:
    published = datetime(2026, 9, 8, tzinfo=UTC)

    first = build_article_id(
        title="First headline",
        url="https://example.com/news/123",
        source="Reuters",
        published_at=published,
    )

    second = build_article_id(
        title="Changed headline",
        url="https://example.com/news/123/",
        source="Reuters",
        published_at=published,
    )

    assert first == second


def test_article_id_is_sha256_length() -> None:
    article_id = build_article_id(
        title="Factory outage",
        url="https://example.com/factory",
        source="Reuters",
        published_at=datetime.now(UTC),
    )

    assert len(article_id) == 64


def test_repository_rejects_duplicate(tmp_path) -> None:
    database = tmp_path / "news.db"

    repository = NewsRepository(database)

    published = datetime(2026, 9, 8, tzinfo=UTC)

    article_id = build_article_id(
        title="Semiconductor factory outage",
        url="https://example.com/article",
        source="Reuters",
        published_at=published,
    )

    article = NewsArticle(
        article_id=article_id,
        title="Semiconductor factory outage",
        description="Production temporarily stopped.",
        content=None,
        url="https://example.com/article",
        source="Reuters",
        published_at=published,
        ingested_at=datetime.now(UTC),
    )

    assert repository.save(article) is True
    assert repository.save(article) is False
    assert repository.count() == 1


def test_new_article_processing_flags_are_zero(
    tmp_path,
) -> None:
    database = tmp_path / "news.db"

    repository = NewsRepository(database)

    published = datetime(2026, 9, 8, tzinfo=UTC)

    article = NewsArticle(
        article_id=build_article_id(
            title="Lithium supply disruption",
            url="https://example.com/lithium",
            source="Test Source",
            published_at=published,
        ),
        title="Lithium supply disruption",
        url="https://example.com/lithium",
        source="Test Source",
        published_at=published,
        ingested_at=datetime.now(UTC),
    )

    repository.save(article)

    with repository._connect() as connection:
        row = connection.execute(
            """
            SELECT
                nlp_processed,
                classification_processed,
                graph_injected
            FROM news_articles
            WHERE article_id = ?
            """,
            (article.article_id,),
        ).fetchone()

    assert row["nlp_processed"] == 0
    assert row["classification_processed"] == 0
    assert row["graph_injected"] == 0