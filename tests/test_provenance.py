import pytest
from pydantic import ValidationError

from src.graph.provenance.models import (
    ExtractedRelationship,
    ProvenanceMetadata,
)
from src.graph.provenance.repository import (
    RELATIONSHIP_SCHEMA,
)


def test_provenance_metadata_valid() -> None:
    provenance = ProvenanceMetadata(
        source="SEC_EDGAR",
        source_document="0001045810-25-000023",
        filing_date="2025-02-26",
        extraction_method="spacy_triplet",
        confidence=0.91,
    )

    assert provenance.source == "SEC_EDGAR"
    assert provenance.confidence == 0.91
    assert provenance.filing_date.isoformat() == "2025-02-26"


def test_confidence_cannot_exceed_one() -> None:
    with pytest.raises(ValidationError):
        ProvenanceMetadata(
            source="SEC_EDGAR",
            source_document="test-doc",
            extraction_method="spacy_triplet",
            confidence=1.5,
        )


def test_confidence_cannot_be_negative() -> None:
    with pytest.raises(ValidationError):
        ProvenanceMetadata(
            source="SEC_EDGAR",
            source_document="test-doc",
            extraction_method="spacy_triplet",
            confidence=-0.1,
        )


def test_extracted_relationship_keeps_provenance() -> None:
    relationship = ExtractedRelationship(
        source_entity="NVIDIA",
        relationship_type="DEPENDS_ON",
        target_entity="TSMC",
        provenance=ProvenanceMetadata(
            source="SEC_EDGAR",
            source_document="nvidia-10k",
            extraction_method="spacy_triplet",
            confidence=0.92,
        ),
    )

    assert relationship.source_entity == "NVIDIA"
    assert relationship.target_entity == "TSMC"
    assert relationship.provenance.source == "SEC_EDGAR"
    assert relationship.provenance.confidence == 0.92


def test_relationship_schema_contains_expected_types() -> None:
    assert "SUPPLIES" in RELATIONSHIP_SCHEMA
    assert "DEPENDS_ON" in RELATIONSHIP_SCHEMA
    assert "OPERATES" in RELATIONSHIP_SCHEMA
    assert "USES" in RELATIONSHIP_SCHEMA
    assert "PRODUCES" in RELATIONSHIP_SCHEMA


def test_produces_supports_product_and_material() -> None:
    source_label, target_labels = RELATIONSHIP_SCHEMA["PRODUCES"]

    assert source_label == "Company"
    assert "Product" in target_labels
    assert "Material" in target_labels


def test_uses_supports_material_and_technology() -> None:
    source_label, target_labels = RELATIONSHIP_SCHEMA["USES"]

    assert source_label == "Company"
    assert "Material" in target_labels
    assert "Technology" in target_labels