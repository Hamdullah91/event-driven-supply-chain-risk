from __future__ import annotations

import json
from collections.abc import Mapping
from typing import Any

import httpx

from src.agent.llm import LLMProviderError


class OpenAIStructuredLLM:
    """Production StructuredLLM adapter backed by OpenAI's Responses API."""

    def __init__(
        self,
        *,
        api_key: str,
        model: str,
        base_url: str = "https://api.openai.com/v1",
        timeout_seconds: float = 30.0,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        if not api_key.strip():
            raise ValueError("OpenAI API key must not be blank")
        if not model.strip():
            raise ValueError("OpenAI model must not be blank")
        self.api_key = api_key.strip()
        self.model = model.strip()
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds
        self.client = client

    async def complete_json(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
    ) -> Mapping[str, Any]:
        # OpenAI JSON mode requires the conversation input to explicitly mention
        # JSON. Keep that transport requirement inside the adapter so every
        # structured Agent call satisfies it without coupling domain prompts to
        # provider-specific behavior.
        json_input = f"Return a JSON object only.\n\n{user_prompt}"
        payload = {
            "model": self.model,
            "instructions": system_prompt,
            "input": json_input,
            "text": {"format": {"type": "json_object"}},
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        try:
            if self.client is not None:
                response = await self.client.post(
                    f"{self.base_url}/responses",
                    headers=headers,
                    json=payload,
                    timeout=self.timeout_seconds,
                )
            else:
                async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                    response = await client.post(
                        f"{self.base_url}/responses",
                        headers=headers,
                        json=payload,
                    )
        except httpx.RequestError as exc:
            raise LLMProviderError(
                f"OpenAI Responses API request failed before a response was received: {type(exc).__name__}."
            ) from exc

        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            detail = self._extract_error_detail(response)
            raise LLMProviderError(
                f"OpenAI Responses API returned HTTP {response.status_code}: {detail}"
            ) from exc

        try:
            data = response.json()
        except ValueError as exc:
            raise LLMProviderError(
                "OpenAI Responses API returned an invalid JSON response."
            ) from exc

        text = self._extract_output_text(data)
        try:
            parsed = json.loads(text)
        except json.JSONDecodeError as exc:
            raise ValueError("OpenAI response was not valid JSON") from exc
        if not isinstance(parsed, dict):
            raise ValueError("OpenAI structured response must be a JSON object")
        return parsed

    @staticmethod
    def _extract_error_detail(response: httpx.Response) -> str:
        try:
            data = response.json()
        except ValueError:
            text = response.text.strip()
            return text[:500] if text else "provider returned no error detail"

        if isinstance(data, Mapping):
            error = data.get("error")
            if isinstance(error, Mapping):
                parts: list[str] = []
                code = error.get("code")
                error_type = error.get("type")
                message = error.get("message")
                if isinstance(code, str) and code.strip():
                    parts.append(f"code={code.strip()}")
                if isinstance(error_type, str) and error_type.strip():
                    parts.append(f"type={error_type.strip()}")
                if isinstance(message, str) and message.strip():
                    parts.append(message.strip()[:400])
                if parts:
                    return "; ".join(parts)

        return "provider returned an unrecognized error payload"

    @staticmethod
    def _extract_output_text(data: Mapping[str, Any]) -> str:
        direct = data.get("output_text")
        if isinstance(direct, str) and direct.strip():
            return direct
        output = data.get("output")
        if isinstance(output, list):
            for item in output:
                if not isinstance(item, Mapping):
                    continue
                content = item.get("content")
                if not isinstance(content, list):
                    continue
                for part in content:
                    if isinstance(part, Mapping):
                        text = part.get("text")
                        if isinstance(text, str) and text.strip():
                            return text
        raise ValueError("OpenAI response did not contain output text")
