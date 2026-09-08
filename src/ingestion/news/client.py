from __future__ import annotations

import asyncio
import logging
import random
from datetime import UTC, datetime
from typing import Any

import httpx

from src.ingestion.news.models import NewsArticle, build_article_id


logger = logging.getLogger(__name__)


class NewsAPIError(RuntimeError):
    """Raised when the News API cannot be queried successfully."""


class NewsAPIClient:
    RETRYABLE_STATUS_CODES = {
        408,
        429,
        500,
        502,
        503,
        504,
    }

    def __init__(
        self,
        *,
        api_url: str,
        api_key: str,
        timeout_seconds: float = 20.0,
        max_retries: int = 4,
    ) -> None:
        if not api_key:
            raise ValueError("News API key cannot be empty.")

        self.api_url = api_url
        self.max_retries = max_retries

        self._client = httpx.AsyncClient(
            timeout=httpx.Timeout(timeout_seconds),
            headers={
                "X-Api-Key": api_key,
                "User-Agent": "event-driven-supply-chain-risk/1.0",
            },
        )

    async def __aenter__(self) -> "NewsAPIClient":
        return self

    async def __aexit__(
        self,
        exc_type: Any,
        exc: BaseException | None,
        traceback: Any,
    ) -> None:
        await self.close()

    async def close(self) -> None:
        await self._client.aclose()

    async def fetch_articles(
        self,
        *,
        query: str,
        from_time: datetime | None = None,
    ) -> list[NewsArticle]:

        params: dict[str, Any] = {
            "q": query,
            "language": "en",
            "sortBy": "publishedAt",
            "pageSize": 100,
            "page": 1,
        }

        if from_time is not None:
            params["from"] = from_time.isoformat()

        response = await self._request_with_retry(
            params=params
        )

        payload = response.json()

        if payload.get("status") != "ok":
            raise NewsAPIError(
                payload.get(
                    "message",
                    "News API returned an invalid response.",
                )
            )

        raw_articles = payload.get("articles", [])

        articles: list[NewsArticle] = []

        for raw_article in raw_articles:
            article = self._normalize_article(
                raw_article
            )

            if article is not None:
                articles.append(article)

        logger.info(
            "Normalized %d news articles.",
            len(articles),
        )

        return articles

    async def _request_with_retry(
        self,
        *,
        params: dict[str, Any],
    ) -> httpx.Response:

        last_exception: Exception | None = None

        for attempt in range(1, self.max_retries + 1):
            try:
                logger.info(
                    "News API request attempt=%d",
                    attempt,
                )

                response = await self._client.get(
                    self.api_url,
                    params=params,
                )

                if (
                    response.status_code
                    in self.RETRYABLE_STATUS_CODES
                ):
                    raise NewsAPIError(
                        f"Retryable HTTP status "
                        f"{response.status_code}"
                    )

                response.raise_for_status()

                return response

            except (
                httpx.TimeoutException,
                httpx.NetworkError,
                NewsAPIError,
            ) as exc:
                last_exception = exc

                logger.warning(
                    "News API request failed "
                    "attempt=%d error=%s",
                    attempt,
                    exc,
                )

                if attempt >= self.max_retries:
                    break

                delay = self._calculate_backoff(
                    attempt
                )

                logger.info(
                    "Retrying in %.2f seconds.",
                    delay,
                )

                await asyncio.sleep(delay)

            except httpx.HTTPStatusError as exc:
                logger.error(
                    "Non-retryable News API error "
                    "status=%d",
                    exc.response.status_code,
                )
                raise NewsAPIError(
                    f"News API returned HTTP "
                    f"{exc.response.status_code}"
                ) from exc

        raise NewsAPIError(
            f"News API failed after "
            f"{self.max_retries} attempts."
        ) from last_exception

    @staticmethod
    def _calculate_backoff(
        attempt: int,
    ) -> float:
        delay = 2 ** attempt
        jitter = random.uniform(0.0, 1.0)

        return min(delay + jitter, 30.0)

    @staticmethod
    def _normalize_article(
        raw_article: dict[str, Any],
    ) -> NewsArticle | None:

        title = (raw_article.get("title") or "").strip()
        url = (raw_article.get("url") or "").strip()
        published_raw = raw_article.get("publishedAt")

        if not title or not url or not published_raw:
            logger.warning(
                "Skipping article with missing "
                "required fields."
            )
            return None

        try:
            published_at = datetime.fromisoformat(
                published_raw.replace(
                    "Z",
                    "+00:00",
                )
            )
        except ValueError:
            logger.warning(
                "Skipping article with invalid "
                "timestamp=%r",
                published_raw,
            )
            return None

        source_data = raw_article.get("source") or {}

        source = (
            source_data.get("name")
            or "unknown"
        )

        article_id = build_article_id(
            title=title,
            url=url,
            source=source,
            published_at=published_at,
        )

        return NewsArticle(
            article_id=article_id,
            title=title,
            description=raw_article.get("description"),
            content=raw_article.get("content"),
            url=url,
            source=source,
            published_at=published_at,
            ingested_at=datetime.now(UTC),
        )