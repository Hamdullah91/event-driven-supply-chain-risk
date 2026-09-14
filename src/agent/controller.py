from __future__ import annotations

from src.agent.cypher_generator import CypherGenerator
from src.agent.cypher_validator import CypherValidator
from src.agent.evidence import assess_evidence
from src.agent.explainer import GroundedExplainer, GroundedExplanation
from src.agent.graph_inspector import GraphInspector
from src.agent.models import AgentPlan, CypherProposal
from src.agent.planner import AgentPlanner


class AgentController:
    """Orchestrate safe graph preparation and optional grounded explanation."""

    def __init__(
        self,
        *,
        planner: AgentPlanner,
        cypher_generator: CypherGenerator,
        cypher_validator: CypherValidator | None = None,
        graph_inspector: GraphInspector | None = None,
        explainer: GroundedExplainer | None = None,
    ) -> None:
        self.planner = planner
        self.cypher_generator = cypher_generator
        self.cypher_validator = cypher_validator or CypherValidator()
        self.graph_inspector = graph_inspector
        self.explainer = explainer or GroundedExplainer()

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

    async def answer(self, question: str) -> GroundedExplanation:
        """Run the graph path through inspection and deterministic explanation."""
        _, proposal = await self.prepare(question)

        if proposal is None:
            raise ValueError(
                "This question does not produce a graph query; use its deterministic tool route."
            )
        if self.graph_inspector is None:
            raise RuntimeError(
                "AgentController.answer() requires a configured GraphInspector."
            )

        bundle = self.graph_inspector.inspect(
            question=question,
            proposal=proposal,
            validator=self.cypher_validator,
        )
        assessment = assess_evidence(bundle)
        return self.explainer.explain(bundle=bundle, assessment=assessment)
