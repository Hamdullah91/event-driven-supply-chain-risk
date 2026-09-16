from __future__ import annotations

from pydantic import BaseModel, Field

from src.agent.evidence import (
    EvidenceAssessment,
    EvidenceBundle,
    EvidenceStatus,
    EventEvidence,
    GraphNodeEvidence,
    GraphPathEvidence,
)


RELATIONSHIP_EXPLANATIONS = {
    "DEPENDS_ON": "depends on",
    "SUPPLIES": "supplies",
    "USES": "uses",
    "PRODUCES": "produces",
    "OPERATES": "operates",
    "OWNS": "owns",
    "LOCATED_IN": "is located in",
    "AFFECTS": "affects",
    "OCCURS_AT": "occurs at",
}

EVENT_LABELS = {
    "SUPPLY_DISRUPTION": "supply disruption",
    "FACILITY_OUTAGE": "facility outage",
    "REGULATION_CHANGE": "regulatory change",
    "TECHNOLOGY_EMBARGO": "technology embargo",
    "TRADE_POLICY_CHANGE": "trade-policy disruption",
    "RAW_MATERIAL_SHORTAGE": "raw-material shortage",
}


class GroundedExplanation(BaseModel):
    answer: str = Field(min_length=1)
    evidence_status: EvidenceStatus
    affected_entities: list[str] = Field(default_factory=list)
    dependency_paths: list[list[str]] = Field(default_factory=list)
    hop_counts: list[int] = Field(default_factory=list)
    event_refs: list[str] = Field(default_factory=list)
    path_ids: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class GroundedExplainer:
    """Convert validated graph evidence into deterministic natural language."""

    def explain(
        self,
        *,
        bundle: EvidenceBundle,
        assessment: EvidenceAssessment,
    ) -> GroundedExplanation:
        if assessment.status is EvidenceStatus.INSUFFICIENT:
            return self._insufficient_explanation(assessment)

        path_by_id = {path.path_id: path for path in bundle.paths}
        event_by_ref = {event.ref: event for event in bundle.events}

        sentences: list[str] = []
        dependency_paths: list[list[str]] = []
        hop_counts: list[int] = []
        path_ids: list[str] = []
        affected_entities: list[str] = []
        described_event_refs: set[str] = set()

        for finding in assessment.relevant_paths:
            path = path_by_id.get(finding.path_id)
            if path is None or not finding.entities:
                continue

            dependency_paths.append(finding.entities)
            hop_counts.append(finding.hop_count)
            path_ids.append(finding.path_id)

            path_text = " → ".join(finding.entities)
            exposure_word = "direct" if finding.hop_count == 1 else "indirect"
            sentences.append(
                f"The graph identifies the {exposure_word} dependency path {path_text}, "
                f"spanning {self._hop_phrase(finding.hop_count)}."
            )

            relationship_sentences = self._relationship_sentences(path)
            if relationship_sentences:
                sentences.extend(relationship_sentences)

            for event_ref in finding.linked_events:
                if event_ref in described_event_refs:
                    continue
                event = event_by_ref.get(event_ref)
                if event is None:
                    continue
                event_sentence = self._event_sentence(event)
                if event_sentence:
                    sentences.append(event_sentence)
                    described_event_refs.add(event_ref)
                if event.linked_entity_name and event.linked_entity_name not in affected_entities:
                    affected_entities.append(event.linked_entity_name)

        if assessment.status is EvidenceStatus.PARTIAL:
            sentences.append(
                "The available graph evidence is partial, so the requested disruption linkage "
                "cannot be fully established."
            )
            sentences.extend(assessment.missing_evidence)

        if not sentences:
            return self._insufficient_explanation(assessment)

        return GroundedExplanation(
            answer=self._join_sentences(sentences),
            evidence_status=assessment.status,
            affected_entities=affected_entities,
            dependency_paths=dependency_paths,
            hop_counts=hop_counts,
            event_refs=assessment.relevant_events,
            path_ids=path_ids,
            warnings=[*bundle.warnings, *assessment.missing_evidence],
        )

    def _insufficient_explanation(
        self,
        assessment: EvidenceAssessment,
    ) -> GroundedExplanation:
        answer = (
            "The current knowledge graph does not contain sufficient validated evidence "
            "to establish the requested supply-chain risk relationship."
        )
        if assessment.missing_evidence:
            answer += " " + " ".join(assessment.missing_evidence)

        return GroundedExplanation(
            answer=answer,
            evidence_status=EvidenceStatus.INSUFFICIENT,
            warnings=assessment.missing_evidence,
        )

    def _relationship_sentences(self, path: GraphPathEvidence) -> list[str]:
        nodes_by_ref = {node.ref: node for node in path.nodes}
        sentences: list[str] = []

        for relationship in path.relationships:
            source = nodes_by_ref.get(relationship.start_node_ref or "")
            target = nodes_by_ref.get(relationship.end_node_ref or "")
            if source is None or target is None:
                continue

            phrase = RELATIONSHIP_EXPLANATIONS.get(
                relationship.relationship_type,
                relationship.relationship_type.lower().replace("_", " "),
            )
            sentences.append(
                f"{self._display_name(source)} {phrase} {self._display_name(target)}."
            )

        return sentences

    def _event_sentence(self, event: EventEvidence) -> str | None:
        if not event.linked_entity_name:
            return None

        if event.event_type:
            event_label = EVENT_LABELS.get(
                event.event_type,
                event.event_type.lower().replace("_", " "),
            )
            sentence = (
                f"A linked {event_label} event affects {event.linked_entity_name}"
                if event.linkage_type == "AFFECTS"
                else f"A linked {event_label} event is associated with {event.linked_entity_name}"
            )
        else:
            sentence = f"A linked event is associated with {event.linked_entity_name}"

        details: list[str] = []
        if event.event_id:
            details.append(f"event {event.event_id}")
        if event.severity is not None:
            details.append(f"severity {event.severity.value}")
        if event.confidence is not None:
            details.append(f"confidence {event.confidence:.2f}")
        if event.source:
            details.append(f"source {event.source}")

        if details:
            sentence += " (" + ", ".join(details) + ")"
        return sentence + "."

    @staticmethod
    def _join_sentences(sentences: list[str]) -> str:
        return " ".join(sentence.strip() for sentence in sentences if sentence.strip())

    @staticmethod
    def _hop_phrase(hop_count: int) -> str:
        if hop_count == 0:
            return "zero dependency hops"
        if hop_count == 1:
            return "one dependency hop"
        if hop_count == 2:
            return "two dependency hops"
        if hop_count == 3:
            return "three dependency hops"
        return f"{hop_count} dependency hops"

    @staticmethod
    def _display_name(node: GraphNodeEvidence) -> str:
        for key in (
            "name",
            "company_name",
            "facility_name",
            "material_name",
            "product_name",
            "company_id",
            "facility_id",
            "id",
        ):
            value = node.properties.get(key)
            if value not in (None, ""):
                return str(value)
        return node.ref
