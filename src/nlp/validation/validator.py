from __future__ import annotations

from dataclasses import dataclass

from .relationship_rules import VALID_RELATIONSHIPS


@dataclass(frozen=True, slots=True)
class RelationshipCandidate:
    subject: str
    subject_type: str
    relationship: str
    object: str
    object_type: str


@dataclass(frozen=True, slots=True)
class ValidationResult:
    is_valid: bool
    reason: str | None = None


class RelationshipValidator:
    """Validate candidate graph relationships against the project ontology."""

    def validate(
        self,
        candidate: RelationshipCandidate,
    ) -> ValidationResult:

        subject = candidate.subject.strip()
        object_name = candidate.object.strip()

        subject_type = candidate.subject_type.strip()
        object_type = candidate.object_type.strip()

        relationship = candidate.relationship.strip().upper()

        if not subject:
            return ValidationResult(
                is_valid=False,
                reason="Subject cannot be empty.",
            )

        if not object_name:
            return ValidationResult(
                is_valid=False,
                reason="Object cannot be empty.",
            )

        if not subject_type:
            return ValidationResult(
                is_valid=False,
                reason="Subject type cannot be empty.",
            )

        if not object_type:
            return ValidationResult(
                is_valid=False,
                reason="Object type cannot be empty.",
            )

        if not relationship:
            return ValidationResult(
                is_valid=False,
                reason="Relationship cannot be empty.",
            )

        rule = (
            subject_type,
            relationship,
            object_type,
        )

        if rule not in VALID_RELATIONSHIPS:
            return ValidationResult(
                is_valid=False,
                reason=(
                    "Relationship violates graph ontology: "
                    f"{subject_type} -[{relationship}]-> {object_type}"
                ),
            )

        return ValidationResult(
            is_valid=True,
            reason=None,
        )