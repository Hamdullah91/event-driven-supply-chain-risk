from __future__ import annotations

import asyncio
import logging
from datetime import UTC, datetime, timedelta
from time import monotonic

from src.events.pipeline import EventPipeline
from src.ingestion.news.classification import NewsClassificationService
from src.ingestion.news.client import NewsAPIClient, NewsAPIError
from src.ingestion.news.nlp_processor import NewsNLPProcessor
from src.ingestion.news.repository import NewsRepository


logger = logging.getLogger(__name__)


class NewsPoller:
    def __init__(
        self,
        *,
        client: NewsAPIClient,
        repository: NewsRepository,
        query: str,
        poll_interval_seconds: int = 900,
        nlp_processor: NewsNLPProcessor | None = None,
        classification_service: NewsClassificationService | None = None,
        event_pipeline: EventPipeline | None = None,
    ) -> None:
        if poll_interval_seconds <= 0:
            raise ValueError(
                "poll_interval_seconds must be positive."
            )

        self.client = client
        self.repository = repository
        self.query = query
        self.poll_interval_seconds = poll_interval_seconds
        self.nlp_processor = nlp_processor
        self.classification_service = classification_service
        self.event_pipeline = event_pipeline

        self._stop_event = asyncio.Event()
        self._last_poll_time: datetime | None = None

    async def poll_once(self) -> None:
        cycle_started = monotonic()
        started_at = datetime.now(UTC)

        # Small overlap protects against articles appearing
        # near polling boundaries.
        from_time = started_at - timedelta(days=2)

        logger.info(
            "News poll started query=%r from=%s",
            self.query,
            from_time.isoformat(),
        )

        try:
            articles = await self.client.fetch_articles(
                query=self.query,
                from_time=from_time,
            )

        except NewsAPIError:
            logger.exception(
                "News poll failed because the API "
                "could not be queried."
            )
            return

        except Exception:
            logger.exception(
                "Unexpected error during news polling."
            )
            return

        new_count = 0
        duplicate_count = 0

        nlp_processed_count = 0
        nlp_failed_count = 0

        classified_count = 0
        classification_failed_count = 0
        review_count = 0

        event_created_count = 0
        event_failed_count = 0

        for article in articles:
            nlp_result = None
            classified = None

            saved = self.repository.save(article)

            if not saved:
                duplicate_count += 1

                logger.debug(
                    "Duplicate article skipped "
                    "article_id=%s",
                    article.article_id,
                )
                continue

            new_count += 1

            logger.info(
                "Saved article "
                "article_id=%s "
                "source=%s "
                "title=%r",
                article.article_id,
                article.source,
                article.title,
            )

            if self.nlp_processor is not None:
                try:
                    nlp_result = await asyncio.to_thread(
                        self.nlp_processor.process,
                        article,
                    )

                    nlp_processed_count += 1

                    logger.info(
                        "News NLP processed "
                        "article_id=%s "
                        "entities=%d "
                        "resolved_companies=%d "
                        "triplets=%d",
                        article.article_id,
                        len(nlp_result.entities),
                        len(nlp_result.resolved_companies),
                        len(nlp_result.triplets),
                    )

                except Exception:
                    nlp_failed_count += 1

                    logger.exception(
                        "News NLP processing failed "
                        "article_id=%s",
                        article.article_id,
                    )

            if self.classification_service is not None:
                try:
                    classified = await asyncio.to_thread(
                        self.classification_service.classify,
                        article,
                    )

                    classified_count += 1

                    if classified.requires_review:
                        review_count += 1

                    logger.info(
                        "News classification completed "
                        "article_id=%s "
                        "event_type=%s "
                        "confidence=%.4f "
                        "second_event_type=%s "
                        "second_confidence=%.4f "
                        "margin=%.4f "
                        "requires_review=%s",
                        classified.article_id,
                        classified.event_type,
                        classified.confidence,
                        classified.second_event_type,
                        classified.second_confidence,
                        classified.confidence_margin,
                        classified.requires_review,
                    )

                except Exception:
                    classification_failed_count += 1

                    logger.exception(
                        "News classification failed "
                        "article_id=%s",
                        article.article_id,
                    )

            if (
                self.event_pipeline is not None
                and nlp_result is not None
                and classified is not None
                and not classified.requires_review
            ):
                try:
                    pipeline_result = await asyncio.to_thread(
                        self.event_pipeline.process,
                        classified=classified,
                        nlp_result=nlp_result,
                    )

                    event_created_count += 1

                    logger.info(
                        "Dynamic event created "
                        "article_id=%s "
                        "event_id=%s "
                        "linked_companies=%d",
                        article.article_id,
                        pipeline_result.event.event_id,
                        pipeline_result.linked_companies,
                    )

                except Exception:
                    event_failed_count += 1

                    logger.exception(
                        "Dynamic event pipeline failed "
                        "article_id=%s",
                        article.article_id,
                    )
            elif (
                classified is not None
                and classified.requires_review
            ):
                logger.info(
                    "Dynamic event skipped because classification "
                    "requires review "
                    "article_id=%s "
                    "event_type=%s "
                    "confidence=%.4f",
                    classified.article_id,
                    classified.event_type,
                    classified.confidence,
                )
                
        self._last_poll_time = started_at

        duration = monotonic() - cycle_started

        logger.info(
            "News poll finished "
            "fetched=%d "
            "new=%d "
            "duplicates=%d "
            "nlp_processed=%d "
            "nlp_failed=%d "
            "classified=%d "
            "classification_failed=%d "
            "requires_review=%d "
            "events_created=%d "
            "events_failed=%d "
            "duration_seconds=%.3f",
            len(articles),
            new_count,
            duplicate_count,
            nlp_processed_count,
            nlp_failed_count,
            classified_count,
            classification_failed_count,
            review_count,
            event_created_count,
            event_failed_count,
            duration,
        )

    async def run_forever(self) -> None:
        logger.info(
            "News poller started "
            "interval_seconds=%d",
            self.poll_interval_seconds,
        )

        while not self._stop_event.is_set():
            cycle_started = monotonic()

            await self.poll_once()

            cycle_duration = (
                monotonic() - cycle_started
            )

            sleep_seconds = max(
                0.0,
                self.poll_interval_seconds
                - cycle_duration,
            )

            logger.info(
                "Next poll in %.2f seconds.",
                sleep_seconds,
            )

            try:
                await asyncio.wait_for(
                    self._stop_event.wait(),
                    timeout=sleep_seconds,
                )

            except asyncio.TimeoutError:
                pass

        logger.info("News poller stopped.")

    def stop(self) -> None:
        self._stop_event.set()