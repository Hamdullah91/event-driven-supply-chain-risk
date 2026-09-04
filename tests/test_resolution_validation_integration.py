from src.nlp.entity_resolution.models import ResolvedEntity
from src.nlp.validation.resolution_integration import (
    ResolvedRelationshipInput,
    build_candidate_from_resolved_company,
    validate_resolved_relationships,
)


def make_resolved_nvidia() -> ResolvedEntity:
    return ResolvedEntity(
        original_name="NVIDIA",
        normalized_name="nvidia",
        canonical_id="company_nvidia",
        canonical_name="NVIDIA Corporation",
        confidence=1.0,
        resolution_method="alias_exact",
    )


def test_resolved_company_builds_candidate() -> None:
    company = make_resolved_nvidia()

    relationship = ResolvedRelationshipInput(
        subject=company,
        relationship="USES",
        object_name="Silicon",
        object_type="Material",
    )

    candidate = build_candidate_from_resolved_company(
        relationship
    )

    assert candidate is not None
    assert candidate.subject == "NVIDIA Corporation"
    assert candidate.subject_type == "Company"
    assert candidate.relationship == "USES"
    assert candidate.object == "Silicon"
    assert candidate.object_type == "Material"


def test_unresolved_company_is_rejected_before_validation() -> None:
    unresolved = ResolvedEntity(
        original_name="Unknown Corp",
        normalized_name="unknown corp",
        canonical_id=None,
        canonical_name=None,
        confidence=0.0,
        resolution_method="unresolved",
    )

    relationship = ResolvedRelationshipInput(
        subject=unresolved,
        relationship="USES",
        object_name="Silicon",
        object_type="Material",
    )

    candidate = build_candidate_from_resolved_company(
        relationship
    )

    assert candidate is None


def test_valid_resolved_relationship_passes() -> None:
    company = make_resolved_nvidia()

    relationships = [
        ResolvedRelationshipInput(
            subject=company,
            relationship="USES",
            object_name="Silicon",
            object_type="Material",
        )
    ]

    result = validate_resolved_relationships(
        relationships
    )

    assert len(result.valid) == 1
    assert len(result.rejected) == 0

    assert result.valid[0].subject == "NVIDIA Corporation"
    assert result.valid[0].relationship == "USES"
    assert result.valid[0].object == "Silicon"


def test_invalid_resolved_relationship_is_rejected() -> None:
    company = make_resolved_nvidia()

    relationships = [
        ResolvedRelationshipInput(
            subject=company,
            relationship="LOCATED_IN",
            object_name="California",
            object_type="Location",
        )
    ]

    result = validate_resolved_relationships(
        relationships
    )

    assert len(result.valid) == 0
    assert len(result.rejected) == 1

    assert "violates graph ontology" in (
        result.rejected[0].reason
    )


def test_mixed_relationship_batch() -> None:
    company = make_resolved_nvidia()

    relationships = [
        ResolvedRelationshipInput(
            subject=company,
            relationship="USES",
            object_name="Silicon",
            object_type="Material",
        ),
        ResolvedRelationshipInput(
            subject=company,
            relationship="LOCATED_IN",
            object_name="California",
            object_type="Location",
        ),
        ResolvedRelationshipInput(
            subject=company,
            relationship="PRODUCES",
            object_name="GPU",
            object_type="Product",
        ),
    ]

    result = validate_resolved_relationships(
        relationships
    )

    assert len(result.valid) == 2
    assert len(result.rejected) == 1