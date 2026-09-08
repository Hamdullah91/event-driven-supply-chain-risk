from __future__ import annotations

from datetime import datetime, timezone

from src.ingestion.news.models import NewsArticle, build_article_id
from src.ingestion.news.nlp_processor import NewsNLPProcessor


def main() -> None:
    published_at = datetime.now(timezone.utc)

    title = "ASML supplies lithography equipment to TSMC"

    article = NewsArticle(
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

    processor = NewsNLPProcessor()
    result = processor.process(article)

    print("\n=== ENTITIES ===")
    for entity in result.entities:
        print(
            entity.text,
            "|",
            entity.nlp_label,
            "|",
            entity.domain_type,
        )

    print("\n=== RESOLVED COMPANIES ===")
    for company in result.resolved_companies:
        print(company)

    print("\n=== TRIPLETS ===")
    for triplet in result.triplets:
        print(
            triplet.subject,
            "->",
            triplet.predicate,
            "->",
            triplet.object,
        )


if __name__ == "__main__":
    main()