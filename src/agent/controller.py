from __future__ import annotations

from src.agent.cypher_generator import CypherGenerator
from src.agent.models import AgentPlan, CypherProposal
from src.agent.planner import AgentPlanner


class AgentController:
    """Day 50 orchestration boundary: plan, optionally propose Cypher, then stop."""

    def __init__(
        self,
        *,
        planner: AgentPlanner,
        cypher_generator: CypherGenerator,
    ) -> None:
        self.planner = planner
        self.cypher_generator = cypher_generator

    async def prepare(self, question: str) -> tuple[AgentPlan, CypherProposal | None]:
        plan = await self.planner.plan(question)
        proposal: CypherProposal | None = None

        if plan.requires_generated_cypher:
            proposal = await self.cypher_generator.generate(
                question=question,
                plan=plan,
            )

        return plan, proposal
