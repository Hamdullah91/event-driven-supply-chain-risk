from __future__ import annotations

import pytest

from src.agent.cypher_validator import UnsafeCypherError
from src.agent.evidence import (
    EvidenceBundle,
    EvidenceStatus,
    EventEvidence,
    GraphNodeEvidence,
    GraphPathEvidence,
    GraphRelationshipEvidence,
    assess_evidence,
)
from src.agent.graph_inspector import GraphInspector
from src.agent.models import CypherProposal
from src.agent.prompts import build_cypher_system_prompt


class _FakeResult:
    def __init__(self, records):
        self.records = records

    def __iter__(self):
        return iter(self.records)


class _FakeSession:
    def __init__(self, records):
        self.records = records
        self.calls = []

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def run(self, cypher, parameters=None, **kwargs):
        self.calls.append((cypher, parameters, kwargs))
        return _FakeResult(self.records)


class _FakeDriver:
    def __init__(self, records):
        self.session_obj = _FakeSession(records)

    def session(self, **kwargs):
        return self.session_obj


def _path() -> GraphPathEvidence:
    return GraphPathEvidence(
        path_id="P1",
        nodes=[
            GraphNodeEvidence(ref="company:tsmc", labels=["Company"], properties={"name": "TSMC"}),
            GraphNodeEvidence(ref="company:nvidia", labels=["Company"], properties={"name": "NVIDIA"}),
            GraphNodeEvidence(ref="company:dell", labels=["Company"], properties={"name": "Dell"}),
        ],
        relationships=[
            GraphRelationshipEvidence(ref="r1", relationship_type="SUPPLIES"),
            GraphRelationshipEvidence(ref="r2", relationship_type="SUPPLIES"),
        ],
        hop_count=2,
    )


def test_assessment_is_sufficient_when_path_and_linked_event_exist():
    bundle = EvidenceBundle(
        question="How does a TSMC outage affect Dell?",
        cypher="MATCH p=(a)-[:SUPPLIES*1..3]->(b) RETURN p AS path LIMIT 20",
        paths=[_path()],
        events=[
            EventEvidence(
                ref="event:1",
                event_id="evt-1",
                event_type="FACILITY_OUTAGE",
                severity=0.9,
                confidence=0.94,
                source="news-source",
                linked_entity_ref="company:tsmc",
                linkage_type="AFFECTS",
            )
        ],
    )

    assessment = assess_evidence(bundle)

    assert assessment.status is EvidenceStatus.SUFFICIENT
    assert assessment.relevant_paths[0].hop_count == 2
    assert assessment.relevant_paths[0].entities == ["TSMC", "NVIDIA", "Dell"]
    assert assessment.relevant_paths[0].linked_events == ["event:1"]
    assert assessment.relevant_events == ["event:1"]


def test_assessment_is_partial_for_path_without_event():
    bundle = EvidenceBundle(
        question="What path connects TSMC and Dell?",
        cypher="MATCH p=(a)-[:SUPPLIES*1..3]->(b) RETURN p AS path LIMIT 20",
        paths=[_path()],
    )

    assessment = assess_evidence(bundle)

    assert assessment.status is EvidenceStatus.PARTIAL
    assert "No Event node" in assessment.missing_evidence[0]


def test_assessment_is_insufficient_without_path_or_event():
    bundle = EvidenceBundle(
        question="Is Boeing exposed?",
        cypher="MATCH (c:Company) RETURN c LIMIT 20",
    )

    assessment = assess_evidence(bundle)

    assert assessment.status is EvidenceStatus.INSUFFICIENT
    assert len(assessment.missing_evidence) == 2


def test_graph_path_model_rejects_more_than_three_hops():
    with pytest.raises(ValueError):
        GraphPathEvidence(
            path_id="P4",
            nodes=[GraphNodeEvidence(ref="n1")],
            relationships=[],
            hop_count=4,
        )


def test_inspector_validates_before_query_execution(monkeypatch):
    driver = _FakeDriver([])
    inspector = GraphInspector(driver)
    proposal = CypherProposal(cypher="MATCH (n) DELETE n", parameters={})

    with pytest.raises(UnsafeCypherError):
        inspector.inspect(question="Delete everything", proposal=proposal)

    assert driver.session_obj.calls == []


def test_inspector_preserves_query_results_and_warnings(monkeypatch):
    driver = _FakeDriver([{"company": "Dell", "risk_score": 0.468}])
    inspector = GraphInspector(driver)
    proposal = CypherProposal(
        cypher="MATCH (c:Company) RETURN c.name AS company LIMIT 5",
        parameters={},
        expected_fields=["company"],
    )

    monkeypatch.setattr(inspector, "_extract_paths", lambda records: [])
    monkeypatch.setattr(inspector, "_fetch_events", lambda node_refs: [])

    bundle = inspector.inspect(question="Show companies", proposal=proposal)

    assert bundle.query_results == [{"company": "Dell", "risk_score": 0.468}]
    assert len(bundle.warnings) == 2


def test_cypher_prompt_requires_explicit_path_for_explainability():
    prompt = build_cypher_system_prompt()

    assert "RETURN p AS path" in prompt
    assert "Downstream graph inspection" in prompt
