from __future__ import annotations

from dataclasses import dataclass

from src.ingestion.news.models import NewsArticle
from src.nlp.entity_extraction.extractor import EntityExtractor
from src.nlp.entity_extraction.models import ExtractedEntity
from src.nlp.entity_resolution.integration import (
    resolve_extracted_companies,
)
from src.nlp.entity_resolution.models import ResolvedEntity
from src.nlp.triplet_extractor import (
    GraphCandidate,
    TripletExtractor,
)


@dataclass(frozen=True, slots=True)
class NewsNLPResult:
    article_id: str
    entities: list[ExtractedEntity]
    resolved_companies: list[ResolvedEntity]
    triplets: list[GraphCandidate]


class NewsNLPProcessor:
    """
    Apply the existing NLP pipeline to a normalized news article.

    Day 33 responsibilities:
        NewsArticle
            -> spaCy/domain entity extraction
            -> company entity resolution
            -> dependency-based triplet extraction

    This processor does not write anything to Neo4j.
    """

    def __init__(
        self,
        entity_extractor: EntityExtractor | None = None,
    ) -> None:
        self.entity_extractor = (
            entity_extractor or EntityExtractor()
        )

        # Reuse the exact same loaded spaCy Language object.
        # This avoids loading en_core_web_sm twice.
        self.triplet_extractor = TripletExtractor(
            self.entity_extractor.nlp
        )

    @staticmethod
    def _build_article_text(article: NewsArticle) -> str:
        parts = [
            article.title,
            article.description,
            article.content,
        ]

        cleaned_parts = [
            part.strip()
            for part in parts
            if part and part.strip()
        ]

        return "\n".join(cleaned_parts)

    def process(
        self,
        article: NewsArticle,
    ) -> NewsNLPResult:
        text = self._build_article_text(article)

        raw_entities = self.entity_extractor.extract(text)

        entities = list(
            {
                (
                    entity.text.strip().lower(),
                    entity.domain_type,
                ): entity
                for entity in raw_entities
            }.values()
        )
        company_names = [
            entity.text
            for entity in entities
            if entity.domain_type == "Company"
        ]

        resolved_companies = resolve_extracted_companies(
            company_names
        )

        triplets = self.triplet_extractor.extract(text)

        return NewsNLPResult(
            article_id=article.article_id,
            entities=entities,
            resolved_companies=resolved_companies,
            triplets=triplets,
        )