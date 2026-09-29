from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Protocol


class LLMProviderError(RuntimeError):
    """Raised when a configured external LLM provider cannot complete a request."""


class StructuredLLM(Protocol):
    """Provider-neutral boundary for structured LLM responses.

    The agent layer depends on this protocol instead of a vendor SDK so OpenAI,
    Gemini, or another provider can be swapped without changing planner or
    Cypher-generation logic.
    """

    async def complete_json(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
    ) -> Mapping[str, Any]: ...
