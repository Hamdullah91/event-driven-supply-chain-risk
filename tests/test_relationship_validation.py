import pytest

from src.nlp.validation import (
    RelationshipCandidate,
    RelationshipValidator,
)


@pytest.fixture
def validator() -> RelationshipValidator:
    return RelationshipValidator()


@pytest.mark.parametrize(
    ("subject_type", "relationship", "object_type"),
    [
        ("Company", "SUPPLIES", "Company"),
        ("Company", "DEPENDS_ON", "Company"),
        ("Company", "OPERATES", "Facility"),
        ("Company", "OWNS", "Facility"),
        ("Company", "USES", "Material"),
        ("Company", "USES", "Technology"),
        ("Company", "PRODUCES", "Product"),
        ("Company", "PRODUCES", "Material"),
        ("Company", "OPERATES_IN", "Industry"),
        ("Facility", "LOCATED_IN", "Location"),
        ("Location", "LOCATED_IN", "Country"),
        ("Event", "AFFECTS", "Company"),
        ("Event", "AFFECTS", "Facility"),
        ("Event", "OCCURS_AT", "Facility"),
    ],
)
def test_valid_relationships(
    validator: RelationshipValidator,
    subject_type: str,
    relationship: str,
    object_type: str,
) -> None:
    candidate = RelationshipCandidate(
        subject="source",
        subject_type=subject_type,
        relationship=relationship,
        object="target",
        object_type=object_type,
    )

    result = validator.validate(candidate)

    assert result.is_valid is True
    assert result.reason is None


@pytest.mark.parametrize(
    ("subject_type", "relationship", "object_type"),
    [
        ("Material", "SUPPLIES", "Company"),
        ("Company", "LOCATED_IN", "Location"),
        ("Country", "USES", "Material"),
        ("Product", "AFFECTS", "Company"),
        ("Facility", "DEPENDS_ON", "Company"),
        ("Event", "USES", "Technology"),
    ],
)
def test_invalid_relationships(
    validator: RelationshipValidator,
    subject_type: str,
    relationship: str,
    object_type: str,
) -> None:
    candidate = RelationshipCandidate(
        subject="source",
        subject_type=subject_type,
        relationship=relationship,
        object="target",
        object_type=object_type,
    )

    result = validator.validate(candidate)

    assert result.is_valid is False
    assert result.reason is not None


def test_empty_subject_is_rejected(
    validator: RelationshipValidator,
) -> None:
    candidate = RelationshipCandidate(
        subject="",
        subject_type="Company",
        relationship="USES",
        object="Silicon",
        object_type="Material",
    )

    result = validator.validate(candidate)

    assert result.is_valid is False
    assert result.reason == "Subject cannot be empty."


def test_relationship_is_normalized_to_uppercase(
    validator: RelationshipValidator,
) -> None:
    candidate = RelationshipCandidate(
        subject="NVIDIA",
        subject_type="Company",
        relationship="uses",
        object="Silicon",
        object_type="Material",
    )

    result = validator.validate(candidate)

    assert result.is_valid is True