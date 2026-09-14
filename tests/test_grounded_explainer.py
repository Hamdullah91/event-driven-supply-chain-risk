from __future__ import annotations

from src.agent.evidence import (
    EvidenceBundle,
    EvidenceStatus,
    EventEvidence,
    GraphNodeEvidence,
    GraphPathEvidence,
    GraphRelationshipEvidence,
    assess_evidence,
)
from src.agent.explainer import GroundedExplainer


def _bundle(*, hop_count: int = 1, with_event: bool = True) -> EvidenceBundle:
    nodes = [
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
    ]
    relationships = [
        GraphRelationshipEvidence(
            ref="r1",
            relationship_type="DEPENDS_ON",
            start_node_ref="company:nvidia",
            end_node_ref="company:tsmc",
        )
    ]

    if hop_count >= 2:
        nodes.append(
            GraphNodeEvidence(
                ref="company:asml",
                labels=["Company"],
                properties={"name": "ASML"},
            )
        )
        relationships.append(
            GraphRelationshipEvidence(
                ref="r2",
                relationship_type="DEPENDS_ON",
                start_node_ref="company:tsmc",
                end_node_ref="company:asml",
            )
        )

    if hop_count >= 3:
        nodes.append(
            GraphNodeEvidence(
                ref="company:zeiss",
                labels=["Company"],
                properties={"name": "ZEISS"},
            )
        )
        relationships.append(
            GraphRelationshipEvidence(
                ref="r3",
                relationship_type="DEPENDS_ON",
                start_node_ref="company:asml",
                end_node_ref="company:zeiss",
            )
        )

    events = []
    if with_event:
        events.append(
            EventEvidence(
                ref="event:1",
                event_id="evt-1",
                event_type="FACILITY_OUTAGE",
                severity=0.9,
                confidence=0.95,
                source="news-source",
                linked_entity_ref=nodes[-1].ref,
                linked_entity_name=nodes[-1].properties["name"],
                linkage_type="AFFECTS",
            )
        )

    return EvidenceBundle(
        question="How is NVIDIA exposed?",
        cypher="MATCH p=(a)-[:DEPENDS_ON*1..3]->(b) RETURN p AS path LIMIT 20",
        paths=[
            GraphPathEvidence(
                path_id="P1",
                nodes=nodes,
                relationships=relationships,
                hop_count=hop_count,
            )
        ],
        events=events,
    )


def test_explainer_generates_grounded_one_hop_answer():
    bundle = _bundle()
    explanation = GroundedExplainer().explain(
        bundle=bundle,
        assessment=assess_evidence(bundle),
    )

    assert explanation.evidence_status is EvidenceStatus.SUFFICIENT
    assert explanation.hop_counts == [1]
    assert explanation.path_ids == ["P1"]
    assert explanation.event_refs == ["event:1"]
    assert "NVIDIA depends on TSMC" in explanation.answer
    assert "one dependency hop" in explanation.answer
    assert "facility outage" in explanation.answer.lower()


def test_explainer_describes_two_hop_exposure_as_indirect():
    bundle = _bundle(hop_count=2)
    explanation = GroundedExplainer().explain(
        bundle=bundle,
        assessment=assess_evidence(bundle),
    )

    assert explanation.hop_counts == [2]
    assert "NVIDIA → TSMC → ASML" in explanation.answer
    assert "two dependency hops" in explanation.answer
    assert "indirect" in explanation.answer.lower()


def test_explainer_supports_three_hop_paths():
    bundle = _bundle(hop_count=3)
    explanation = GroundedExplainer().explain(
        bundle=bundle,
        assessment=assess_evidence(bundle),
    )

    assert explanation.hop_counts == [3]
    assert "three dependency hops" in explanation.answer
    assert "NVIDIA → TSMC → ASML → ZEISS" in explanation.answer


def test_partial_evidence_states_missing_event_instead_of_claiming_event_exposure():
    bundle = _bundle(with_event=False)
    explanation = GroundedExplainer().explain(
        bundle=bundle,
        assessment=assess_evidence(bundle),
    )

    assert explanation.evidence_status is EvidenceStatus.PARTIAL
    assert "partial" in explanation.answer.lower()
    assert "No Event node" in explanation.answer
    assert explanation.event_refs == []


def test_insufficient_evidence_does_not_claim_exposure():
    bundle = EvidenceBundle(
        question="Is Boeing exposed?",
        cypher="MATCH (c:Company) RETURN c LIMIT 20",
    )
    explanation = GroundedExplainer().explain(
        bundle=bundle,
        assessment=assess_evidence(bundle),
    )

    assert explanation.evidence_status is EvidenceStatus.INSUFFICIENT
    assert "does not contain sufficient" in explanation.answer
    assert "is exposed" not in explanation.answer.lower()
    assert explanation.path_ids == []


def test_explanation_does_not_invent_entities_or_relationships():
    bundle = _bundle()
    explanation = GroundedExplainer().explain(
        bundle=bundle,
        assessment=assess_evidence(bundle),
    )

    assert "Intel" not in explanation.answer
    assert "Samsung" not in explanation.answer
    assert "supplies NVIDIA" not in explanation.answer
