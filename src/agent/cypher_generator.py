from __future__ import annotations

from src.agent.llm import StructuredLLM
from src.agent.models import AgentPlan, CypherProposal, ToolName
from src.agent.prompts import build_cypher_system_prompt


class CypherGenerator:
    """Generate a candidate Cypher proposal without executing it."""

    def __init__(self, llm: StructuredLLM) -> None:
        self.llm = llm

    async def generate(
        self,
        *,
        question: str,
        plan: AgentPlan,
    ) -> CypherProposal:
        if not question.strip():
            raise ValueError("question must not be blank")
        if plan.tool is not ToolName.GRAPH_QUERY:
            raise ValueError("Cypher generation requires the GRAPH_QUERY tool")
        if not plan.requires_generated_cypher:
            raise ValueError("plan does not require generated Cypher")

        user_prompt = (
            f"Question: {question.strip()}\n"
            f"Objective: {plan.objective}\n"
            f"Maximum hops: {plan.max_hops}\n"
            f"Entities: {[entity.model_dump() for entity in plan.entities]}"
        )
        payload = await self.llm.complete_json(
            system_prompt=build_cypher_system_prompt(),
            user_prompt=user_prompt,
        )
        return CypherProposal.model_validate(payload)
