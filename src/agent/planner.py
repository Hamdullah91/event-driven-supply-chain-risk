from __future__ import annotations

from src.agent.llm import StructuredLLM
from src.agent.models import AgentPlan
from src.agent.prompts import PLANNER_SYSTEM_PROMPT


class AgentPlanner:
    """Translate a natural-language question into a structured tool plan."""

    def __init__(self, llm: StructuredLLM) -> None:
        self.llm = llm

    async def plan(self, question: str) -> AgentPlan:
        if not question.strip():
            raise ValueError("question must not be blank")

        payload = await self.llm.complete_json(
            system_prompt=PLANNER_SYSTEM_PROMPT,
            user_prompt=question.strip(),
        )
        return AgentPlan.model_validate(payload)
