from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING, Any

from src.config.settings import Settings
from src.graph.connection import Neo4jConnection

if TYPE_CHECKING:
    from src.ingestion.news.poller import NewsPoller


logger = logging.getLogger(__name__)

DEFAULT_NEWS_QUERY = (
    '"semiconductor" OR "chip shortage" OR "EV battery" OR "lithium" OR '
    '"aerospace" OR "supply chain" OR "factory outage" OR "export restriction"'
)


class NewsPollerRuntime:
    """Own the optional news poller as a FastAPI-process background task.

    Keeping the poller in the API process intentionally lets RiskStreamService
    use the same in-memory ConnectionManager as `/risk-stream` clients. This is
    the smallest architecture that provides real-time delivery for the FYP
    without introducing Redis solely for cross-process fan-out.
    """

    def __init__(self) -> None:
        self.task: asyncio.Task[None] | None = None
        self.poller: NewsPoller | None = None
        self.status: str = "disabled"
        self.last_error: str | None = None

    def snapshot(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "running": self.task is not None and not self.task.done(),
            "last_error": self.last_error,
        }

    async def start(self, *, settings: Settings, connection: Neo4jConnection) -> None:
        if not settings.NEWS_POLLER_ENABLED:
            self.status = "disabled"
            self.last_error = None
            return
        if not settings.NEWS_API_KEY.strip():
            self.status = "unconfigured"
            self.last_error = "NEWS_API_KEY is required when NEWS_POLLER_ENABLED=true."
            return
        if self.task is not None and not self.task.done():
            return

        self.status = "starting"
        self.last_error = None
        self.task = asyncio.create_task(
            self._run(settings=settings, connection=connection),
            name="supply-chain-news-poller",
        )
        await asyncio.sleep(0)

    async def _run(self, *, settings: Settings, connection: Neo4jConnection) -> None:
        # Import heavyweight ML/NLP/runtime dependencies only when the optional
        # poller is actually enabled. Normal FastAPI imports stay lightweight.
        from src.api.services.risk import RiskAnalyticsService
        from src.api.services.risk_stream import RiskStreamService
        from src.events.pipeline import EventPipeline
        from src.graph.repository import GraphRepository
        from src.ingestion.news.classification import NewsClassificationService
        from src.ingestion.news.client import NewsAPIClient
        from src.ingestion.news.nlp_processor import NewsNLPProcessor
        from src.ingestion.news.poller import NewsPoller
        from src.ingestion.news.repository import NewsRepository
        from src.ml.event_classifier import EventClassifier
        from src.risk.repository import RiskRepository

        try:
            repository = NewsRepository(settings.NEWS_DATABASE_PATH)
            classifier = EventClassifier(
                model_path=settings.EVENT_CLASSIFIER_MODEL_PATH,
                max_length=settings.EVENT_CLASSIFIER_MAX_LENGTH,
                confidence_threshold=settings.EVENT_CLASSIFIER_CONFIDENCE_THRESHOLD,
            )
            classification_service = NewsClassificationService(classifier=classifier)
            nlp_processor = NewsNLPProcessor()
            graph_repository = GraphRepository(connection)
            event_pipeline = EventPipeline(graph_repository=graph_repository)
            risk_service = RiskAnalyticsService(RiskRepository(connection))
            risk_stream_service = RiskStreamService(risk_service)

            async with NewsAPIClient(
                api_url=settings.NEWS_API_URL,
                api_key=settings.NEWS_API_KEY,
                timeout_seconds=settings.NEWS_REQUEST_TIMEOUT_SECONDS,
                max_retries=settings.NEWS_MAX_RETRIES,
            ) as client:
                self.poller = NewsPoller(
                    client=client,
                    repository=repository,
                    query=DEFAULT_NEWS_QUERY,
                    poll_interval_seconds=settings.NEWS_POLL_INTERVAL_SECONDS,
                    nlp_processor=nlp_processor,
                    classification_service=classification_service,
                    event_pipeline=event_pipeline,
                    risk_stream_service=risk_stream_service,
                )
                self.status = "running"
                logger.info("Same-process news poller runtime started.")
                await self.poller.run_forever()
                self.status = "stopped"
        except asyncio.CancelledError:
            self.status = "stopped"
            raise
        except Exception as exc:
            self.status = "failed"
            self.last_error = f"{type(exc).__name__}: {exc}"
            logger.exception("Same-process news poller runtime failed.")
        finally:
            self.poller = None

    async def stop(self) -> None:
        task = self.task
        if task is None:
            if self.status == "running":
                self.status = "stopped"
            return

        if self.poller is not None:
            self.poller.stop()

        if not task.done():
            try:
                await asyncio.wait_for(task, timeout=5.0)
            except TimeoutError:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass

        self.task = None
        if self.status not in {"failed", "unconfigured", "disabled"}:
            self.status = "stopped"


news_poller_runtime = NewsPollerRuntime()
