from __future__ import annotations

from src.agent.cypher_generator import CypherGenerator
from src.agent.cypher_validator import CypherValidator
from src.agent.models import AgentPlan, CypherProposal
from src.agent.planner import AgentPlanner


class AgentController:
    """Plan, generate optional Cypher, validate it, then stop before Neo4j execution."""

    def __init__(
        self,
        *,
        planner: AgentPlanner,
        cypher_generator: CypherGenerator,
        cypher_validator: CypherValidator | None = None,
    ) -> None:
        self.planner = planner
        self.cypher_generator = cypher_generator
        self.cypher_validator = cypher_validator or CypherValidator()

    async def prepare(self, question: str) -> tuple[AgentPlan, CypherProposal | None]:
        plan = await self.planner.plan(question)
        proposal: CypherProposal | None = None

        if plan.requires_generated_cypher:
            proposal = await self.cypher_generator.generate(
                question=question,
                plan=plan,
            )
            self.cypher_validator.ensure_safe(proposal)

        return plan, proposal
