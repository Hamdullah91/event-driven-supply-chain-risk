from __future__ import annotations

import asyncio
import logging
import signal
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

from src.ingestion.news.client import NewsAPIClient
from src.ingestion.news.poller import NewsPoller
from src.ingestion.news.repository import NewsRepository


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    news_api_key: str
    news_api_url: str = "https://newsapi.org/v2/everything"

    news_poll_interval_seconds: int = 900
    news_request_timeout_seconds: float = 20.0
    news_max_retries: int = 4

    news_database_path: str = "data/news/news.db"
    news_log_path: str = "logs/news_poller.log"


def configure_logging(log_path: str) -> None:
    path = Path(log_path)

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | "
        "%(name)s | %(message)s"
    )

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    file_handler = logging.FileHandler(
        path,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)

    logging.basicConfig(
        level=logging.INFO,
        handlers=[
            console_handler,
            file_handler,
        ],
    )


async def main() -> None:
    settings = Settings()

    configure_logging(
        settings.news_log_path
    )

    logger = logging.getLogger(__name__)

    repository = NewsRepository(
        settings.news_database_path
    )

    query = (
        '"semiconductor" OR '
        '"chip shortage" OR '
        '"EV battery" OR '
        '"lithium" OR '
        '"aerospace" OR '
        '"supply chain" OR '
        '"factory outage" OR '
        '"export restriction"'
    )

    async with NewsAPIClient(
        api_url=settings.news_api_url,
        api_key=settings.news_api_key,
        timeout_seconds=(
            settings.news_request_timeout_seconds
        ),
        max_retries=settings.news_max_retries,
    ) as client:

        poller = NewsPoller(
            client=client,
            repository=repository,
            query=query,
            poll_interval_seconds=(
                settings.news_poll_interval_seconds
            ),
        )

        loop = asyncio.get_running_loop()

        for sig in (
            signal.SIGINT,
            signal.SIGTERM,
        ):
            try:
                loop.add_signal_handler(
                    sig,
                    poller.stop,
                )
            except NotImplementedError:
                # Expected on some Windows event loops.
                pass

        logger.info(
            "Starting Day 32 news polling service."
        )

        await poller.run_forever()


if __name__ == "__main__":
    asyncio.run(main())