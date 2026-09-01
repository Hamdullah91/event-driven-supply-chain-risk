from __future__ import annotations

import asyncio

import httpx
import pytest

from src.ingestion.sec.client import (
    SECClient,
    SECClientError,
    SECNotFoundError,
)


def create_client(
    *,
    max_retries: int = 2,
) -> SECClient:
    return SECClient(
        user_agent="TestApp test@example.com",
        requests_per_second=1000,
        max_retries=max_retries,
        timeout_seconds=5,
    )


def test_retry_after_header_is_respected() -> None:
    client = create_client()

    response = httpx.Response(
        status_code=429,
        headers={
            "Retry-After": "3",
        },
    )

    delay = client._retry_delay(
        response,
        attempt=0,
    )

    assert delay == 3.0

    asyncio.run(client.close())


def test_invalid_retry_after_uses_backoff(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = create_client()

    response = httpx.Response(
        status_code=429,
        headers={
            "Retry-After": "invalid",
        },
    )

    monkeypatch.setattr(
        client,
        "_backoff_seconds",
        lambda attempt: 2.5,
    )

    delay = client._retry_delay(
        response,
        attempt=0,
    )

    assert delay == 2.5

    asyncio.run(client.close())


def test_429_response_is_retried(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = create_client(
        max_retries=2,
    )

    request = httpx.Request(
        "GET",
        "https://example.com/test",
    )

    responses = [
        httpx.Response(
            status_code=429,
            headers={
                "Retry-After": "0",
            },
            request=request,
        ),
        httpx.Response(
            status_code=200,
            content=b"success",
            request=request,
        ),
    ]

    call_count = 0

    async def fake_get(
        url: str,
    ) -> httpx.Response:
        nonlocal call_count

        response = responses[call_count]
        call_count += 1

        return response

    async def fake_sleep(
        delay: float,
    ) -> None:
        return None

    async def fake_acquire() -> None:
        return None

    monkeypatch.setattr(
        client._client,
        "get",
        fake_get,
    )

    monkeypatch.setattr(
        asyncio,
        "sleep",
        fake_sleep,
    )

    monkeypatch.setattr(
        client._rate_limiter,
        "acquire",
        fake_acquire,
    )

    response = asyncio.run(
        client._request(
            "https://example.com/test"
        )
    )

    assert response.status_code == 200
    assert call_count == 2

    asyncio.run(client.close())


def test_500_response_is_retried(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = create_client(
        max_retries=2,
    )

    request = httpx.Request(
        "GET",
        "https://example.com/test",
    )

    responses = [
        httpx.Response(
            status_code=503,
            request=request,
        ),
        httpx.Response(
            status_code=200,
            content=b"success",
            request=request,
        ),
    ]

    call_count = 0

    async def fake_get(
        url: str,
    ) -> httpx.Response:
        nonlocal call_count

        response = responses[call_count]
        call_count += 1

        return response

    async def fake_sleep(
        delay: float,
    ) -> None:
        return None

    async def fake_acquire() -> None:
        return None

    monkeypatch.setattr(
        client._client,
        "get",
        fake_get,
    )

    monkeypatch.setattr(
        asyncio,
        "sleep",
        fake_sleep,
    )

    monkeypatch.setattr(
        client._rate_limiter,
        "acquire",
        fake_acquire,
    )

    response = asyncio.run(
        client._request(
            "https://example.com/test"
        )
    )

    assert response.status_code == 200
    assert call_count == 2

    asyncio.run(client.close())


def test_network_error_is_retried(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = create_client(
        max_retries=2,
    )

    call_count = 0

    async def fake_get(
        url: str,
    ) -> httpx.Response:
        nonlocal call_count

        call_count += 1

        if call_count == 1:
            raise httpx.ConnectError(
                "temporary connection failure"
            )

        request = httpx.Request(
            "GET",
            url,
        )

        return httpx.Response(
            status_code=200,
            content=b"success",
            request=request,
        )

    async def fake_sleep(
        delay: float,
    ) -> None:
        return None

    async def fake_acquire() -> None:
        return None

    monkeypatch.setattr(
        client._client,
        "get",
        fake_get,
    )

    monkeypatch.setattr(
        asyncio,
        "sleep",
        fake_sleep,
    )

    monkeypatch.setattr(
        client._rate_limiter,
        "acquire",
        fake_acquire,
    )

    response = asyncio.run(
        client._request(
            "https://example.com/test"
        )
    )

    assert response.status_code == 200
    assert call_count == 2

    asyncio.run(client.close())


def test_retry_exhaustion_raises_client_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = create_client(
        max_retries=1,
    )

    request = httpx.Request(
        "GET",
        "https://example.com/test",
    )

    call_count = 0

    async def fake_get(
        url: str,
    ) -> httpx.Response:
        nonlocal call_count

        call_count += 1

        return httpx.Response(
            status_code=503,
            request=request,
        )

    async def fake_sleep(
        delay: float,
    ) -> None:
        return None

    async def fake_acquire() -> None:
        return None

    monkeypatch.setattr(
        client._client,
        "get",
        fake_get,
    )

    monkeypatch.setattr(
        asyncio,
        "sleep",
        fake_sleep,
    )

    monkeypatch.setattr(
        client._rate_limiter,
        "acquire",
        fake_acquire,
    )

    with pytest.raises(
        SECClientError,
        match="after retries",
    ):
        asyncio.run(
            client._request(
                "https://example.com/test"
            )
        )

    assert call_count == 2

    asyncio.run(client.close())


def test_404_raises_not_found_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = create_client()

    request = httpx.Request(
        "GET",
        "https://example.com/missing",
    )

    async def fake_get(
        url: str,
    ) -> httpx.Response:
        return httpx.Response(
            status_code=404,
            request=request,
        )

    async def fake_acquire() -> None:
        return None

    monkeypatch.setattr(
        client._client,
        "get",
        fake_get,
    )

    monkeypatch.setattr(
        client._rate_limiter,
        "acquire",
        fake_acquire,
    )

    with pytest.raises(
        SECNotFoundError,
        match="resource not found",
    ):
        asyncio.run(
            client._request(
                "https://example.com/missing"
            )
        )

    asyncio.run(client.close())


def test_non_retryable_http_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = create_client()

    request = httpx.Request(
        "GET",
        "https://example.com/test",
    )

    async def fake_get(
        url: str,
    ) -> httpx.Response:
        return httpx.Response(
            status_code=403,
            request=request,
        )

    async def fake_acquire() -> None:
        return None

    monkeypatch.setattr(
        client._client,
        "get",
        fake_get,
    )

    monkeypatch.setattr(
        client._rate_limiter,
        "acquire",
        fake_acquire,
    )

    with pytest.raises(
        SECClientError,
        match="Non-retryable SEC HTTP error",
    ):
        asyncio.run(
            client._request(
                "https://example.com/test"
            )
        )

    asyncio.run(client.close())