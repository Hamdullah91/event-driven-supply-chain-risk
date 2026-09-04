from __future__ import annotations

from dataclasses import dataclass

from src.nlp.entity_resolution.models import ResolvedEntity
from src.nlp.validation.integration import (
    RelationshipValidationPipeline,
    ValidationBatchResult,
)
from src.nlp.validation.validator import RelationshipCandidate


@dataclass(frozen=True, slots=True)
class ResolvedRelationshipInput:
    subject: ResolvedEntity
    relationship: str
    object_name: str
    object_type: str


def build_candidate_from_resolved_company(
    relationship_input: ResolvedRelationshipInput,
) -> RelationshipCandidate | None:
    """
    Convert a resolved company relationship into a validation candidate.

    Returns None when the company could not be resolved.
    """

    subject = relationship_input.subject

    if subject.canonical_id is None or subject.canonical_name is None:
        return None

    return RelationshipCandidate(
        subject=subject.canonical_name,
        subject_type="Company",
        relationship=relationship_input.relationship,
        object=relationship_input.object_name,
        object_type=relationship_input.object_type,
    )


def validate_resolved_relationships(
    relationships: list[ResolvedRelationshipInput],
) -> ValidationBatchResult:
    """
    Convert resolved entities into graph relationship candidates and
    validate them against the ontology.
    """

    candidates: list[RelationshipCandidate] = []

    for relationship in relationships:
        candidate = build_candidate_from_resolved_company(
            relationship
        )

        if candidate is not None:
            candidates.append(candidate)

    pipeline = RelationshipValidationPipeline()

    return pipeline.process(candidates)