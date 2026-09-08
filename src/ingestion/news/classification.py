from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime

from src.ingestion.news.models import NewsArticle
from src.ml.event_classifier import (
    ClassificationResult,
    EventClassifier,
)

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ClassifiedNewsArticle:
    article_id: str

    title: str
    url: str
    source: str

    published_at: datetime
    ingested_at: datetime

    event_type: str
    confidence: float
    requires_review: bool

    second_event_type: str
    second_confidence: float
    confidence_margin: float


class NewsClassificationService:
    """
    Connects normalized NewsArticle objects to the
    fine-tuned DistilBERT event classifier.
    """

    def __init__(
        self,
        *,
        classifier: EventClassifier,
    ) -> None:
        self.classifier = classifier

    @staticmethod
    def build_article_text(
        article: NewsArticle,
    ) -> str:
        parts = [
            article.title,
            article.description,
            article.content,
        ]

        text = " ".join(
            part.strip()
            for part in parts
            if part and part.strip()
        )

        if not text:
            raise ValueError(
                f"Article {article.article_id} "
                "contains no classifiable text."
            )

        return text

    def classify(
        self,
        article: NewsArticle,
    ) -> ClassifiedNewsArticle:
        text = self.build_article_text(article)

        result: ClassificationResult = (
            self.classifier.classify(text)
        )

        logger.info(
            (
                "News article classified "
                "article_id=%s "
                "event_type=%s "
                "confidence=%.4f "
                "requires_review=%s"
            ),
            article.article_id,
            result.event_type,
            result.confidence,
            result.requires_review,
        )

        return ClassifiedNewsArticle(
            article_id=article.article_id,
            title=article.title,
            url=article.url,
            source=article.source,
            published_at=article.published_at,
            ingested_at=article.ingested_at,
            event_type=result.event_type,
            confidence=result.confidence,
            requires_review=result.requires_review,
            second_event_type=result.second_event_type,
            second_confidence=result.second_confidence,
            confidence_margin=result.confidence_margin,
        )