from __future__ import annotations

import logging
from dataclasses import dataclass

from src.events.builder import build_news_event
from src.events.models import SupplyChainEvent
from src.graph.repository import GraphRepository
from src.ingestion.news.classification import ClassifiedNewsArticle
from src.ingestion.news.nlp_processor import NewsNLPResult


logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class EventPipelineResult:
    event: SupplyChainEvent
    linked_companies: int
    failed_company_links: int
    linked_company_ids: tuple[str, ...] = ()


class EventPipeline:
    """Persist classified news events and link them to resolved companies."""

    def __init__(self, *, graph_repository: GraphRepository) -> None:
        self.graph_repository = graph_repository

    def process(
        self,
        *,
        classified: ClassifiedNewsArticle,
        nlp_result: NewsNLPResult,
    ) -> EventPipelineResult:
        if classified.article_id != nlp_result.article_id:
            raise ValueError("Classification and NLP results belong to different articles.")
        if classified.requires_review:
            raise ValueError(
                "Classification requires review; "
                f"article_id={classified.article_id} "
                f"event_type={classified.event_type} "
                f"confidence={classified.confidence:.4f}"
            )

        resolved_companies = [
            entity
            for entity in nlp_result.resolved_companies
            if entity.canonical_id is not None
        ]
        primary_company = (
            max(resolved_companies, key=lambda entity: entity.confidence)
            if resolved_companies
            else None
        )
        entity_id = primary_company.canonical_id if primary_company else None

        event = build_news_event(
            article_id=classified.article_id,
            classifier_label=classified.event_type,
            source=classified.source,
            timestamp=classified.published_at,
            confidence=classified.confidence,
            title=classified.title,
            entity_id=entity_id,
            source_url=classified.url,
        )
        self.graph_repository.save_event(event)

        linked_company_ids: list[str] = []
        failed_company_links = 0
        for resolved in resolved_companies:
            assert resolved.canonical_id is not None
            linked = self.graph_repository.link_event_to_company(
                event_id=str(event.event_id),
                company_id=resolved.canonical_id,
                confidence=resolved.confidence,
                link_method=resolved.resolution_method,
            )
            if linked:
                if resolved.canonical_id not in linked_company_ids:
                    linked_company_ids.append(resolved.canonical_id)
            else:
                failed_company_links += 1
                logger.warning(
                    "Could not link event to company event_id=%s company_id=%s",
                    event.event_id,
                    resolved.canonical_id,
                )

        logger.info(
            "Dynamic event pipeline completed article_id=%s event_id=%s "
            "event_type=%s classification_confidence=%.4f "
            "linked_companies=%d failed_company_links=%d",
            classified.article_id,
            event.event_id,
            classified.event_type,
            classified.confidence,
            len(linked_company_ids),
            failed_company_links,
        )
        return EventPipelineResult(
            event=event,
            linked_companies=len(linked_company_ids),
            failed_company_links=failed_company_links,
            linked_company_ids=tuple(linked_company_ids),
        )
