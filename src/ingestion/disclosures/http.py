from __future__ import annotations

import asyncio
import random
from collections.abc import Mapping

import httpx


RETRYABLE_STATUS_CODES = {408, 425, 429, 500, 502, 503, 504}
RETRYABLE_EXCEPTIONS = (
    httpx.ConnectError,
    httpx.ConnectTimeout,
    httpx.ReadTimeout,
    httpx.RemoteProtocolError,
)


def _backoff_seconds(attempt: int) -> float:
    return min(2**attempt, 16) + random.uniform(0.0, 0.35)


def _retry_delay(response: httpx.Response, attempt: int) -> float:
    retry_after = response.headers.get("Retry-After")
    if retry_after:
        try:
            return max(float(retry_after), 0.0)
        except ValueError:
            pass
    return _backoff_seconds(attempt)


async def get_with_retries(
    client: httpx.AsyncClient,
    url: str,
    *,
    params: Mapping[str, object] | None = None,
    max_retries: int = 4,
) -> httpx.Response:
    """GET with bounded exponential backoff and Retry-After support."""

    for attempt in range(max_retries + 1):
        try:
            response = await client.get(url, params=params)
        except RETRYABLE_EXCEPTIONS:
            if attempt >= max_retries:
                raise
            await asyncio.sleep(_backoff_seconds(attempt))
            continue

        if response.status_code in RETRYABLE_STATUS_CODES:
            if attempt >= max_retries:
                response.raise_for_status()
            await asyncio.sleep(_retry_delay(response, attempt))
            continue

        response.raise_for_status()
        return response

    raise RuntimeError(f"Unexpected HTTP retry termination for {url}")
