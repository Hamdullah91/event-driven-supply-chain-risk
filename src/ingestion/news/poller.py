from __future__ import annotations

import asyncio
import logging
from datetime import UTC, datetime, timedelta
from time import monotonic

from src.ingestion.news.client import NewsAPIClient, NewsAPIError
from src.ingestion.news.repository import NewsRepository
from src.ingestion.news.nlp_processor import NewsNLPProcessor

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

        self._stop_event = asyncio.Event()
        self._last_poll_time: datetime | None = None
    async def poll_once(self) -> None:
        cycle_started = monotonic()
        started_at = datetime.now(UTC)

        # Small overlap protects against articles appearing
        # near polling boundaries.
        if self._last_poll_time is None:
            from_time = started_at - timedelta(days=2)
        else:
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

        for article in articles:
            saved = self.repository.save(article)

            if saved:
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
                        result = await asyncio.to_thread(
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
                            len(result.entities),
                            len(result.resolved_companies),
                            len(result.triplets),
                        )

                    except Exception:
                        nlp_failed_count += 1

                        logger.exception(
                            "News NLP processing failed "
                            "article_id=%s",
                            article.article_id,
                        )

            else:
                duplicate_count += 1

                logger.debug(
                    "Duplicate article skipped "
                    "article_id=%s",
                    article.article_id,
                )

        self._last_poll_time = started_at

        duration = monotonic() - cycle_started

        logger.info(
            "News poll finished "
            "fetched=%d "
            "new=%d "
            "duplicates=%d "
            "duration_seconds=%.3f",
            len(articles),
            new_count,
            duplicate_count,
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

        logger.info(
            "News poll finished "
            "fetched=%d "
            "new=%d "
            "duplicates=%d "
            "duration_seconds=%.3f",
            len(articles),
            new_count,
            duplicate_count,
            duration,
        )

    def stop(self) -> None:
        self._stop_event.set()