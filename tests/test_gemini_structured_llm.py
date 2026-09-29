import asyncio

import httpx
import pytest

from src.agent.gemini_llm import GeminiStructuredLLM
from src.agent.llm import LLMProviderError


def test_gemini_structured_llm_returns_json_object() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/v1beta/models/gemini-2.5-flash-lite:generateContent"
        assert request.headers["x-goog-api-key"] == "test-key"
        payload = __import__("json").loads(request.content)
        assert payload["systemInstruction"]["parts"][0]["text"] == "system"
        assert payload["contents"][0]["parts"][0]["text"] == "question"
        assert payload["generationConfig"]["responseMimeType"] == "application/json"
        return httpx.Response(
            200,
            json={
                "candidates": [
                    {
                        "content": {
                            "parts": [
                                {
                                    "text": '{"intent":"GRAPH_LOOKUP"}',
                                }
                            ]
                        }
                    }
                ]
            },
        )

    async def run() -> dict:
        transport = httpx.MockTransport(handler)
        async with httpx.AsyncClient(transport=transport) as client:
            llm = GeminiStructuredLLM(
                api_key="test-key",
                model="gemini-2.5-flash-lite",
                base_url="https://generativelanguage.googleapis.com/v1beta",
                client=client,
            )
            return dict(
                await llm.complete_json(
                    system_prompt="system",
                    user_prompt="question",
                )
            )

    assert asyncio.run(run()) == {"intent": "GRAPH_LOOKUP"}


def test_gemini_structured_llm_surfaces_provider_http_error() -> None:
    async def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(
            429,
            json={
                "error": {
                    "code": 429,
                    "status": "RESOURCE_EXHAUSTED",
                    "message": "Free-tier quota exceeded.",
                }
            },
        )

    async def run() -> None:
        transport = httpx.MockTransport(handler)
        async with httpx.AsyncClient(transport=transport) as client:
            llm = GeminiStructuredLLM(
                api_key="test-key",
                model="gemini-2.5-flash-lite",
                client=client,
            )
            await llm.complete_json(
                system_prompt="system",
                user_prompt="question",
            )

    with pytest.raises(
        LLMProviderError,
        match=r"HTTP 429: .*RESOURCE_EXHAUSTED.*Free-tier quota exceeded",
    ):
        asyncio.run(run())


def test_gemini_structured_llm_surfaces_transport_error() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("connection failed", request=request)

    async def run() -> None:
        transport = httpx.MockTransport(handler)
        async with httpx.AsyncClient(transport=transport) as client:
            llm = GeminiStructuredLLM(
                api_key="test-key",
                model="gemini-2.5-flash-lite",
                client=client,
            )
            await llm.complete_json(
                system_prompt="system",
                user_prompt="question",
            )

    with pytest.raises(LLMProviderError, match="ConnectError"):
        asyncio.run(run())


def test_gemini_structured_llm_reports_blocked_prompt() -> None:
    async def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={"promptFeedback": {"blockReason": "SAFETY"}},
        )

    async def run() -> None:
        transport = httpx.MockTransport(handler)
        async with httpx.AsyncClient(transport=transport) as client:
            llm = GeminiStructuredLLM(
                api_key="test-key",
                model="gemini-2.5-flash-lite",
                client=client,
            )
            await llm.complete_json(
                system_prompt="system",
                user_prompt="question",
            )

    with pytest.raises(ValueError, match="blocked: SAFETY"):
        asyncio.run(run())


def test_gemini_structured_llm_requires_credentials() -> None:
    with pytest.raises(ValueError, match="API key"):
        GeminiStructuredLLM(api_key="", model="gemini-2.5-flash-lite")
    with pytest.raises(ValueError, match="model"):
        GeminiStructuredLLM(api_key="test-key", model="")
