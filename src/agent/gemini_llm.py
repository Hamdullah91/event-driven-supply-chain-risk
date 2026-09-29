from __future__ import annotations

import json
from collections.abc import Mapping
from typing import Any

import httpx

from src.agent.llm import LLMProviderError


class GeminiStructuredLLM:
    """Production StructuredLLM adapter backed by the Gemini generateContent API."""

    def __init__(
        self,
        *,
        api_key: str,
        model: str,
        base_url: str = "https://generativelanguage.googleapis.com/v1beta",
        timeout_seconds: float = 30.0,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        if not api_key.strip():
            raise ValueError("Gemini API key must not be blank")
        if not model.strip():
            raise ValueError("Gemini model must not be blank")
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
        payload = {
            "systemInstruction": {
                "parts": [{"text": system_prompt}],
            },
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": user_prompt}],
                }
            ],
            "generationConfig": {
                "responseMimeType": "application/json",
            },
        }
        headers = {
            "x-goog-api-key": self.api_key,
            "Content-Type": "application/json",
        }
        url = f"{self.base_url}/models/{self.model}:generateContent"

        try:
            if self.client is not None:
                response = await self.client.post(
                    url,
                    headers=headers,
                    json=payload,
                    timeout=self.timeout_seconds,
                )
            else:
                async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                    response = await client.post(
                        url,
                        headers=headers,
                        json=payload,
                    )
        except httpx.RequestError as exc:
            raise LLMProviderError(
                "Gemini generateContent request failed before a response was "
                f"received: {type(exc).__name__}."
            ) from exc

        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            detail = self._extract_error_detail(response)
            raise LLMProviderError(
                f"Gemini generateContent returned HTTP {response.status_code}: {detail}"
            ) from exc

        try:
            data = response.json()
        except ValueError as exc:
            raise LLMProviderError(
                "Gemini generateContent returned an invalid JSON response."
            ) from exc

        text = self._extract_output_text(data)
        try:
            parsed = json.loads(text)
        except json.JSONDecodeError as exc:
            raise ValueError("Gemini response was not valid JSON") from exc
        if not isinstance(parsed, dict):
            raise ValueError("Gemini structured response must be a JSON object")
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
                status = error.get("status")
                message = error.get("message")
                if isinstance(code, int):
                    parts.append(f"code={code}")
                if isinstance(status, str) and status.strip():
                    parts.append(f"status={status.strip()}")
                if isinstance(message, str) and message.strip():
                    parts.append(message.strip()[:400])
                if parts:
                    return "; ".join(parts)

        return "provider returned an unrecognized error payload"

    @staticmethod
    def _extract_output_text(data: Mapping[str, Any]) -> str:
        candidates = data.get("candidates")
        if isinstance(candidates, list):
            for candidate in candidates:
                if not isinstance(candidate, Mapping):
                    continue
                content = candidate.get("content")
                if not isinstance(content, Mapping):
                    continue
                parts = content.get("parts")
                if not isinstance(parts, list):
                    continue
                for part in parts:
                    if not isinstance(part, Mapping):
                        continue
                    if part.get("thought") is True:
                        continue
                    text = part.get("text")
                    if isinstance(text, str) and text.strip():
                        return text

        prompt_feedback = data.get("promptFeedback")
        if isinstance(prompt_feedback, Mapping):
            block_reason = prompt_feedback.get("blockReason")
            if isinstance(block_reason, str) and block_reason.strip():
                raise ValueError(
                    f"Gemini response was blocked: {block_reason.strip()}"
                )

        raise ValueError("Gemini response did not contain output text")
