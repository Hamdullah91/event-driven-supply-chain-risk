import asyncio
from collections.abc import Mapping
from typing import Any

from src.agent.models import Intent, ToolName
from src.agent.planner import AgentPlanner


class CapturingStructuredLLM:
    def __init__(self) -> None:
        self.system_prompt = ""
        self.user_prompt = ""

    async def complete_json(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
    ) -> Mapping[str, Any]:
        self.system_prompt = system_prompt
        self.user_prompt = user_prompt
        return {
            "intent": "GRAPH_LOOKUP",
            "tool": "COMPANY_NETWORK",
            "objective": "Determine how NVIDIA is connected to TSMC.",
            "entities": [
                {"name": "NVIDIA", "entity_type": "Company"},
                {"name": "TSMC", "entity_type": "Company"},
            ],
            "requires_generated_cypher": False,
            "max_hops": 3,
        }


def test_planner_sends_authoritative_agent_plan_schema() -> None:
    llm = CapturingStructuredLLM()
    planner = AgentPlanner(llm)

    plan = asyncio.run(planner.plan("How is NVIDIA connected to TSMC?"))

    assert plan.intent is Intent.GRAPH_LOOKUP
    assert plan.tool is ToolName.COMPANY_NETWORK
    assert plan.objective == "Determine how NVIDIA is connected to TSMC."
    assert [entity.name for entity in plan.entities] == ["NVIDIA", "TSMC"]

    assert llm.user_prompt == "How is NVIDIA connected to TSMC?"
    assert "AGENTPLAN JSON SCHEMA" in llm.system_prompt
    assert '"required":["intent","tool","objective"]' in llm.system_prompt
    assert '"requires_generated_cypher"' in llm.system_prompt
    assert '"max_hops"' in llm.system_prompt
    assert "Never rename AgentPlan fields" in llm.system_prompt
