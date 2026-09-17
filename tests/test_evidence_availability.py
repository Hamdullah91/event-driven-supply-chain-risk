from src.provenance import (
    EvidenceAvailability,
    event_evidence_availability,
    relationship_evidence_availability,
)


def test_event_evidence_available_when_core_provenance_is_present() -> None:
    assert event_evidence_availability(
        {
            "source": "Reuters",
            "timestamp": "2026-09-17T00:00:00Z",
            "confidence": 0.92,
            "description": "Factory shutdown",
        }
    ) is EvidenceAvailability.AVAILABLE


def test_event_evidence_partial_when_only_some_metadata_is_present() -> None:
    assert event_evidence_availability(
        {"source": "Reuters", "timestamp": None, "confidence": None}
    ) is EvidenceAvailability.PARTIAL


def test_event_evidence_unavailable_without_provenance() -> None:
    assert event_evidence_availability({}) is EvidenceAvailability.UNAVAILABLE


def test_relationship_evidence_available_for_seeded_verified_link() -> None:
    assert relationship_evidence_availability(
        {
            "source_type": "official_company_source",
            "verification_status": "verified",
        }
    ) is EvidenceAvailability.AVAILABLE


def test_relationship_evidence_partial_for_single_support_signal() -> None:
    assert relationship_evidence_availability(
        {"link_method": "alias_exact"}
    ) is EvidenceAvailability.PARTIAL


def test_relationship_evidence_unavailable_without_metadata() -> None:
    assert relationship_evidence_availability({}) is EvidenceAvailability.UNAVAILABLE
