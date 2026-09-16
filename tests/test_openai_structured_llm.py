import asyncio

import httpx
import pytest

from src.agent.openai_llm import OpenAIStructuredLLM


def test_openai_structured_llm_returns_json_object() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/v1/responses"
        assert request.headers["authorization"] == "Bearer test-key"
        payload = __import__("json").loads(request.content)
        assert payload["model"] == "test-model"
        assert payload["instructions"] == "system"
        assert payload["input"] == "question"
        return httpx.Response(
            200,
            json={"output": [{"content": [{"type": "output_text", "text": '{"intent":"GRAPH_LOOKUP"}'}]}]},
        )

    async def run() -> dict:
        transport = httpx.MockTransport(handler)
        async with httpx.AsyncClient(transport=transport) as client:
            llm = OpenAIStructuredLLM(api_key="test-key", model="test-model", client=client)
            return dict(await llm.complete_json(system_prompt="system", user_prompt="question"))

    assert asyncio.run(run()) == {"intent": "GRAPH_LOOKUP"}


def test_openai_structured_llm_rejects_non_json_output() -> None:
    async def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"output_text": "not json"})

    async def run() -> None:
        transport = httpx.MockTransport(handler)
        async with httpx.AsyncClient(transport=transport) as client:
            llm = OpenAIStructuredLLM(api_key="test-key", model="test-model", client=client)
            await llm.complete_json(system_prompt="system", user_prompt="question")

    with pytest.raises(ValueError, match="not valid JSON"):
        asyncio.run(run())


def test_openai_structured_llm_requires_credentials() -> None:
    with pytest.raises(ValueError, match="API key"):
        OpenAIStructuredLLM(api_key="", model="test-model")
    with pytest.raises(ValueError, match="model"):
        OpenAIStructuredLLM(api_key="test-key", model="")
