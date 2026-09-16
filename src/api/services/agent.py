from __future__ import annotations

from src.agent.controller import AgentController
from src.agent.explainer import GroundedExplanation


class AgentQueryService:
    """Public API boundary around the validated Agentic Graph RAG controller."""

    def __init__(self, controller: AgentController) -> None:
        self.controller = controller

    async def answer(self, question: str) -> GroundedExplanation:
        return await self.controller.answer(question)
