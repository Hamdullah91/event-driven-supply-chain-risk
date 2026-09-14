from __future__ import annotations

import asyncio
from collections.abc import Mapping
from typing import Any

import pytest

from src.agent.controller import AgentController
from src.agent.cypher_generator import CypherGenerator
from src.agent.models import AgentPlan, Intent, ToolName
from src.agent.planner import AgentPlanner
from src.agent.schema import build_graph_schema_context


class FakeStructuredLLM:
    def __init__(self, responses: list[Mapping[str, Any]]) -> None:
        self.responses = list(responses)
        self.calls: list[dict[str, str]] = []

    async def complete_json(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
    ) -> Mapping[str, Any]:
        self.calls.append(
            {
                "system_prompt": system_prompt,
                "user_prompt": user_prompt,
            }
        )
        return self.responses.pop(0)


def test_schema_context_uses_project_relationship_dictionary() -> None:
    schema = build_graph_schema_context()

    assert "(:Company)-[:SUPPLIES]->(:Company)" in schema
    assert "(:Company)-[:OPERATES]->(:Facility)" in schema
    assert "(:Event)-[:AFFECTS]->(:Company)" in schema
    assert "company_id" in schema
    assert "event_id" in schema


def test_planner_routes_risk_question_to_existing_risk_engine() -> None:
    llm = FakeStructuredLLM(
        [
            {
                "intent": "RISK_ANALYSIS",
                "tool": "RISK_ENGINE",
                "objective": "Retrieve NVIDIA's current calculated risk",
                "entities": [{"name": "NVIDIA", "entity_type": "Company"}],
                "requires_generated_cypher": False,
                "max_hops": 3,
            }
        ]
    )
    planner = AgentPlanner(llm)

    plan = asyncio.run(planner.plan("What is NVIDIA's current risk?"))

    assert plan.intent is Intent.RISK_ANALYSIS
    assert plan.tool is ToolName.RISK_ENGINE
    assert plan.requires_generated_cypher is False
    assert plan.entities[0].name == "NVIDIA"


def test_generator_returns_parameterized_cypher_proposal() -> None:
    llm = FakeStructuredLLM(
        [
            {
                "cypher": (
                    "MATCH (c:Company {company_id: $company_id})-"
                    "[:DEPENDS_ON*1..3]->(supplier:Company) "
                    "RETURN supplier.company_id AS company_id, length(p) AS hop_distance "
                    "LIMIT 50"
                ),
                "parameters": {"company_id": "nvidia"},
                "expected_fields": ["company_id", "hop_distance"],
            }
        ]
    )
    generator = CypherGenerator(llm)
    plan = AgentPlan(
        intent=Intent.GRAPH_LOOKUP,
        tool=ToolName.GRAPH_QUERY,
        objective="Find upstream dependencies for NVIDIA",
        entities=[{"name": "NVIDIA", "entity_type": "Company"}],
        requires_generated_cypher=True,
        max_hops=3,
    )

    proposal = asyncio.run(
        generator.generate(
            question="Which companies does NVIDIA depend on within three hops?",
            plan=plan,
        )
    )

    assert "$company_id" in proposal.cypher
    assert proposal.parameters == {"company_id": "nvidia"}
    assert proposal.expected_fields == ["company_id", "hop_distance"]
    assert "GRAPH SCHEMA" in llm.calls[0]["system_prompt"]
    assert "Maximum hops: 3" in llm.calls[0]["user_prompt"]


def test_generator_refuses_non_graph_tool_plan() -> None:
    generator = CypherGenerator(FakeStructuredLLM([]))
    plan = AgentPlan(
        intent=Intent.RISK_ANALYSIS,
        tool=ToolName.RISK_ENGINE,
        objective="Calculate risk",
        requires_generated_cypher=False,
    )

    with pytest.raises(ValueError, match="GRAPH_QUERY"):
        asyncio.run(generator.generate(question="Risk to Tesla?", plan=plan))


def test_controller_stops_after_cypher_proposal_without_database_execution() -> None:
    llm = FakeStructuredLLM(
        [
            {
                "intent": "GRAPH_LOOKUP",
                "tool": "GRAPH_QUERY",
                "objective": "Find companies depending on TSMC",
                "entities": [{"name": "TSMC", "entity_type": "Company"}],
                "requires_generated_cypher": True,
                "max_hops": 3,
            },
            {
                "cypher": (
                    "MATCH (supplier:Company {company_id: $company_id})"
                    "<-[:DEPENDS_ON*1..3]-(company:Company) "
                    "RETURN company.company_id AS company_id LIMIT 50"
                ),
                "parameters": {"company_id": "tsmc"},
                "expected_fields": ["company_id"],
            },
        ]
    )
    planner = AgentPlanner(llm)
    generator = CypherGenerator(llm)
    controller = AgentController(planner=planner, cypher_generator=generator)

    plan, proposal = asyncio.run(
        controller.prepare("Which companies depend on TSMC within three hops?")
    )

    assert plan.tool is ToolName.GRAPH_QUERY
    assert proposal is not None
    assert proposal.parameters["company_id"] == "tsmc"
    assert len(llm.calls) == 2


def test_controller_does_not_generate_cypher_for_deterministic_tool() -> None:
    llm = FakeStructuredLLM(
        [
            {
                "intent": "RISK_ANALYSIS",
                "tool": "RISK_ENGINE",
                "objective": "Retrieve Tesla risk",
                "entities": [{"name": "Tesla", "entity_type": "Company"}],
                "requires_generated_cypher": False,
                "max_hops": 3,
            }
        ]
    )
    controller = AgentController(
        planner=AgentPlanner(llm),
        cypher_generator=CypherGenerator(llm),
    )

    plan, proposal = asyncio.run(controller.prepare("What is Tesla's risk?"))

    assert plan.tool is ToolName.RISK_ENGINE
    assert proposal is None
    assert len(llm.calls) == 1
