from __future__ import annotations

import asyncio
import logging
import random
from typing import Any

import httpx

from .rate_limiter import AsyncRateLimiter


logger = logging.getLogger(__name__)


class SECClientError(RuntimeError):
    pass


class SECNotFoundError(SECClientError):
    pass


class SECClient:
    BASE_DATA_URL = "https://data.sec.gov"
    BASE_ARCHIVES_URL = "https://www.sec.gov/Archives"

    RETRYABLE_STATUS_CODES = {
        408,
        425,
        429,
        500,
        502,
        503,
        504,
    }

    def __init__(
        self,
        *,
        user_agent: str,
        requests_per_second: float = 8.0,
        max_retries: int = 5,
        timeout_seconds: float = 30.0,
    ) -> None:
        if not user_agent.strip():
            raise ValueError("SEC user agent cannot be empty")

        if max_retries < 0:
            raise ValueError("max_retries cannot be negative")

        self._max_retries = max_retries
        self._rate_limiter = AsyncRateLimiter(requests_per_second)

        self._client = httpx.AsyncClient(
            headers={
                "User-Agent": user_agent,
                "Accept-Encoding": "gzip, deflate",
                "Accept": "*/*",
            },
            timeout=httpx.Timeout(timeout_seconds),
            follow_redirects=True,
        )

    async def __aenter__(self) -> "SECClient":
        return self

    async def __aexit__(
        self,
        exc_type: object,
        exc: object,
        traceback: object,
    ) -> None:
        await self.close()

    async def close(self) -> None:
        await self._client.aclose()

    async def _request(self, url: str) -> httpx.Response:
        for attempt in range(self._max_retries + 1):
            await self._rate_limiter.acquire()

            try:
                response = await self._client.get(url)

            except (
                httpx.ConnectError,
                httpx.ConnectTimeout,
                httpx.ReadTimeout,
                httpx.RemoteProtocolError,
            ) as exc:
                if attempt >= self._max_retries:
                    raise SECClientError(
                        f"SEC request failed after retries: {url}"
                    ) from exc

                delay = self._backoff_seconds(attempt)

                logger.warning(
                    "SEC network error url=%s attempt=%s retry_in=%.2fs error=%s",
                    url,
                    attempt + 1,
                    delay,
                    exc,
                )

                await asyncio.sleep(delay)
                continue

            if response.status_code == 404:
                raise SECNotFoundError(f"SEC resource not found: {url}")

            if response.status_code in self.RETRYABLE_STATUS_CODES:
                if attempt >= self._max_retries:
                    raise SECClientError(
                        f"SEC returned HTTP {response.status_code} "
                        f"after retries: {url}"
                    )

                delay = self._retry_delay(response, attempt)

                logger.warning(
                    "SEC retryable response status=%s "
                    "url=%s attempt=%s retry_in=%.2fs",
                    response.status_code,
                    url,
                    attempt + 1,
                    delay,
                )

                await asyncio.sleep(delay)
                continue

            try:
                response.raise_for_status()
            except httpx.HTTPStatusError as exc:
                raise SECClientError(
                    f"Non-retryable SEC HTTP error "
                    f"{response.status_code}: {url}"
                ) from exc

            return response

        raise SECClientError(f"Unexpected retry termination: {url}")

    async def get_json(self, url: str) -> dict[str, Any]:
        response = await self._request(url)

        try:
            payload = response.json()
        except ValueError as exc:
            raise SECClientError(
                f"SEC returned invalid JSON: {url}"
            ) from exc

        if not isinstance(payload, dict):
            raise SECClientError(
                f"Expected JSON object from SEC: {url}"
            )

        return payload

    async def get_bytes(self, url: str) -> bytes:
        response = await self._request(url)
        return response.content

    async def get_company_submissions(
        self,
        normalized_cik: str,
    ) -> dict[str, Any]:
        url = (
            f"{self.BASE_DATA_URL}/submissions/"
            f"CIK{normalized_cik}.json"
        )

        return await self.get_json(url)
    
    async def get_submission_file(
        self,
        filename: str,
    ) -> dict[str, Any]:
        url = (
            f"{self.BASE_DATA_URL}/submissions/"
            f"{filename}"
        )

        return await self.get_json(url)
    @staticmethod
    def _backoff_seconds(attempt: int) -> float:
        base = min(2 ** attempt, 32)
        jitter = random.uniform(0.0, 0.5)
        return base + jitter

    def _retry_delay(
        self,
        response: httpx.Response,
        attempt: int,
    ) -> float:
        retry_after = response.headers.get("Retry-After")

        if retry_after:
            try:
                return max(float(retry_after), 0.0)
            except ValueError:
                logger.debug(
                    "Unable to parse Retry-After=%r",
                    retry_after,
                )

        return self._backoff_seconds(attempt)