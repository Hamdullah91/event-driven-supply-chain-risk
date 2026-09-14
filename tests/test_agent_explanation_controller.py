from __future__ import annotations

import asyncio

from src.agent.controller import AgentController
from src.agent.evidence import (
    EvidenceBundle,
    EventEvidence,
    GraphNodeEvidence,
    GraphPathEvidence,
    GraphRelationshipEvidence,
)
from src.agent.models import AgentPlan, CypherProposal, Intent, ToolName


class _Planner:
    async def plan(self, question: str) -> AgentPlan:
        return AgentPlan(
            intent=Intent.GRAPH_LOOKUP,
            tool=ToolName.GRAPH_QUERY,
            objective="Explain NVIDIA exposure to TSMC",
            entities=[
                {"name": "NVIDIA", "entity_type": "Company"},
                {"name": "TSMC", "entity_type": "Company"},
            ],
            requires_generated_cypher=True,
            max_hops=3,
        )


class _Generator:
    async def generate(self, *, question: str, plan: AgentPlan) -> CypherProposal:
        return CypherProposal(
            cypher=(
                "MATCH p=(a:Company {company_id: $company_id})-"
                "[:DEPENDS_ON*1..3]->(b:Company) RETURN p AS path LIMIT 20"
            ),
            parameters={"company_id": "nvidia"},
            expected_fields=["path"],
        )


class _Inspector:
    def __init__(self) -> None:
        self.calls = []

    def inspect(self, *, question, proposal, validator):
        self.calls.append((question, proposal, validator))
        return EvidenceBundle(
            question=question,
            cypher=proposal.cypher,
            paths=[
                GraphPathEvidence(
                    path_id="P1",
                    nodes=[
                        GraphNodeEvidence(
                            ref="company:nvidia",
                            labels=["Company"],
                            properties={"name": "NVIDIA"},
                        ),
                        GraphNodeEvidence(
                            ref="company:tsmc",
                            labels=["Company"],
                            properties={"name": "TSMC"},
                        ),
                    ],
                    relationships=[
                        GraphRelationshipEvidence(
                            ref="r1",
                            relationship_type="DEPENDS_ON",
                            start_node_ref="company:nvidia",
                            end_node_ref="company:tsmc",
                        )
                    ],
                    hop_count=1,
                )
            ],
            events=[
                EventEvidence(
                    ref="event:1",
                    event_id="evt-1",
                    event_type="FACILITY_OUTAGE",
                    linked_entity_ref="company:tsmc",
                    linked_entity_name="TSMC",
                    linkage_type="AFFECTS",
                )
            ],
        )


def test_controller_answer_runs_inspection_and_grounded_explanation():
    inspector = _Inspector()
    controller = AgentController(
        planner=_Planner(),
        cypher_generator=_Generator(),
        graph_inspector=inspector,
    )

    explanation = asyncio.run(
        controller.answer("How does a TSMC outage affect NVIDIA?")
    )

    assert len(inspector.calls) == 1
    assert explanation.path_ids == ["P1"]
    assert explanation.event_refs == ["event:1"]
    assert "NVIDIA depends on TSMC" in explanation.answer
    assert "facility outage" in explanation.answer.lower()


def test_controller_answer_requires_graph_inspector():
    controller = AgentController(
        planner=_Planner(),
        cypher_generator=_Generator(),
    )

    try:
        asyncio.run(controller.answer("How does a TSMC outage affect NVIDIA?"))
    except RuntimeError as exc:
        assert "GraphInspector" in str(exc)
    else:
        raise AssertionError("Expected GraphInspector configuration error")
