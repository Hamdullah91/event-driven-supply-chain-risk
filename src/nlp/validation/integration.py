from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from src.nlp.validation.validator import (
    RelationshipCandidate,
    RelationshipValidator,
    ValidationResult,
)


@dataclass(frozen=True, slots=True)
class ValidatedRelationship:
    subject: str
    subject_type: str
    relationship: str
    object: str
    object_type: str


@dataclass(frozen=True, slots=True)
class RejectedRelationship:
    candidate: RelationshipCandidate
    reason: str


@dataclass(frozen=True, slots=True)
class ValidationBatchResult:
    valid: list[ValidatedRelationship]
    rejected: list[RejectedRelationship]


class RelationshipValidationPipeline:
    """
    Validate resolved NLP relationships before Neo4j ingestion.
    """

    def __init__(
        self,
        validator: RelationshipValidator | None = None,
    ) -> None:
        self.validator = validator or RelationshipValidator()

    def process(
        self,
        candidates: Iterable[RelationshipCandidate],
    ) -> ValidationBatchResult:
        valid: list[ValidatedRelationship] = []
        rejected: list[RejectedRelationship] = []

        for candidate in candidates:
            result: ValidationResult = self.validator.validate(candidate)

            if result.is_valid:
                valid.append(
                    ValidatedRelationship(
                        subject=candidate.subject.strip(),
                        subject_type=candidate.subject_type.strip(),
                        relationship=candidate.relationship.strip().upper(),
                        object=candidate.object.strip(),
                        object_type=candidate.object_type.strip(),
                    )
                )
            else:
                rejected.append(
                    RejectedRelationship(
                        candidate=candidate,
                        reason=result.reason or "Unknown validation failure.",
                    )
                )

        return ValidationBatchResult(
            valid=valid,
            rejected=rejected,
        )