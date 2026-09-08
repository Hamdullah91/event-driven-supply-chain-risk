from __future__ import annotations

from datetime import datetime, timezone

from src.ingestion.news.models import NewsArticle, build_article_id
from src.ingestion.news.nlp_processor import NewsNLPProcessor


def _build_article() -> NewsArticle:
    published_at = datetime.now(timezone.utc)

    title = "ASML supplies lithography equipment to TSMC"

    return NewsArticle(
        article_id=build_article_id(
            title=title,
            url="https://example.com/test-news",
            source="Test News",
            published_at=published_at,
        ),
        title=title,
        description=(
            "ASML supplies advanced lithography equipment to "
            "TSMC for semiconductor manufacturing."
        ),
        content=(
            "TSMC operates major semiconductor facilities "
            "in Taiwan."
        ),
        url="https://example.com/test-news",
        source="Test News",
        published_at=published_at,
        ingested_at=datetime.now(timezone.utc),
    )


def test_news_nlp_extracts_entities() -> None:
    processor = NewsNLPProcessor()
    result = processor.process(_build_article())

    entity_pairs = {
        (entity.text, entity.domain_type)
        for entity in result.entities
    }

    assert ("ASML", "Company") in entity_pairs
    assert ("TSMC", "Company") in entity_pairs
    assert ("semiconductor", "Product") in entity_pairs
    assert ("Taiwan", "Location") in entity_pairs


def test_news_nlp_deduplicates_entities() -> None:
    processor = NewsNLPProcessor()
    result = processor.process(_build_article())

    keys = [
        (
            entity.text.strip().lower(),
            entity.domain_type,
        )
        for entity in result.entities
    ]

    assert len(keys) == len(set(keys))


def test_news_nlp_resolves_companies() -> None:
    processor = NewsNLPProcessor()
    result = processor.process(_build_article())

    resolved = {
        company.original_name: company.canonical_id
        for company in result.resolved_companies
    }

    assert resolved["ASML"] == "company_asml"
    assert resolved["TSMC"] == "company_tsmc"


def test_news_nlp_extracts_supply_relationship() -> None:
    processor = NewsNLPProcessor()
    result = processor.process(_build_article())

    relationships = {
        (
            triplet.subject,
            triplet.predicate,
            triplet.object,
        )
        for triplet in result.triplets
    }

    assert (
        "ASML",
        "SUPPLIES",
        "TSMC",
    ) in relationships