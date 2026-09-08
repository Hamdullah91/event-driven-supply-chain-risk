from __future__ import annotations

from datetime import UTC, datetime

from src.events.pipeline import EventPipeline
from src.graph.connection import Neo4jConnection
from src.graph.repository import GraphRepository
from src.ingestion.news.classification import ClassifiedNewsArticle
from src.ingestion.news.models import NewsArticle, build_article_id
from src.ingestion.news.nlp_processor import NewsNLPProcessor


def main() -> None:
    published_at = datetime.now(UTC)

    title = (
        "TSMC temporarily shut down semiconductor production "
        "after earthquake disruption"
    )

    url = "https://example.com/day37-tsmc-integration-test"

    article = NewsArticle(
        article_id=build_article_id(
            title=title,
            url=url,
            source="day37-integration-test",
            published_at=published_at,
        ),
        title=title,
        description=(
            "TSMC temporarily shut down semiconductor production "
            "at its Taiwan facility after an earthquake disrupted "
            "operations."
        ),
        content=None,
        url=url,
        source="day37-integration-test",
        published_at=published_at,
        ingested_at=datetime.now(UTC),
    )

    print("\n=== DAY 37 CONTROLLED PIPELINE TEST ===")

    # ---------------------------------------------------------
    # 1. Real spaCy + real entity resolution
    # ---------------------------------------------------------
    nlp_processor = NewsNLPProcessor()

    nlp_result = nlp_processor.process(article)

    print("\nNLP entities:")
    for entity in nlp_result.entities:
        print(
            f"  {entity.text} "
            f"-> {entity.domain_type}"
        )

    print("\nResolved companies:")
    for company in nlp_result.resolved_companies:
        print(
            f"  {company.original_name} "
            f"-> {company.canonical_id} "
            f"({company.canonical_name}) "
            f"confidence={company.confidence:.2f}"
        )

    if not nlp_result.resolved_companies:
        raise RuntimeError(
            "Day 37 test failed: "
            "no companies were resolved."
        )

    # ---------------------------------------------------------
    # 2. Controlled classification
    #
    # We already tested the real DistilBERT separately.
    # Here we deliberately provide a high-confidence
    # FACILITY_OUTAGE result to test integration only.
    # ---------------------------------------------------------
    classified = ClassifiedNewsArticle(
        article_id=article.article_id,
        title=article.title,
        url=article.url,
        source=article.source,
        published_at=article.published_at,
        ingested_at=article.ingested_at,
        event_type="FACILITY_OUTAGE",
        confidence=0.95,
        requires_review=False,
        second_event_type="SUPPLY_DISRUPTION",
        second_confidence=0.03,
        confidence_margin=0.92,
    )

    print("\nControlled classification:")
    print(
        f"  event_type={classified.event_type}"
    )
    print(
        f"  confidence={classified.confidence:.2f}"
    )
    print(
        f"  requires_review={classified.requires_review}"
    )

    # ---------------------------------------------------------
    # 3. Real Event builder + real Neo4j persistence/linking
    # ---------------------------------------------------------
    connection = Neo4jConnection()

    try:
        repository = GraphRepository(connection)

        pipeline = EventPipeline(
            graph_repository=repository
        )

        result = pipeline.process(
            classified=classified,
            nlp_result=nlp_result,
        )

        print("\nNeo4j result:")
        print(
            f"  event_id={result.event.event_id}"
        )
        print(
            f"  event_type={result.event.event_type.value}"
        )
        print(
            f"  linked_companies="
            f"{result.linked_companies}"
        )
        print(
            f"  failed_company_links="
            f"{result.failed_company_links}"
        )

        if result.linked_companies < 1:
            raise RuntimeError(
                "Day 37 test failed: "
                "event was not linked to a company."
            )

        print(
            "\nDAY 37 CONTROLLED "
            "END-TO-END TEST: PASSED"
        )

    finally:
        connection.close()


if __name__ == "__main__":
    main()