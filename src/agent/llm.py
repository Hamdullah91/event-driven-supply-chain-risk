from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Protocol


class StructuredLLM(Protocol):
    """Provider-neutral boundary for structured LLM responses.

    The agent layer depends on this protocol instead of a vendor SDK so the
    project can later plug in OpenAI, Llama, or another provider without
    changing planner/generator logic.
    """

    async def complete_json(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
    ) -> Mapping[str, Any]: ...
