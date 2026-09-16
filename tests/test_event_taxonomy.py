from datetime import datetime, timezone

import pytest

from src.events.builder import build_news_event, normalize_classifier_event_type
from src.events.types import EventType


@pytest.mark.parametrize(
    ("classifier_label", "expected"),
    [
        ("SUPPLY_DISRUPTION", EventType.SUPPLY_DISRUPTION),
        ("REGULATION_CHANGE", EventType.REGULATION_CHANGE),
        ("FACILITY_OUTAGE", EventType.FACILITY_OUTAGE),
        ("TECHNOLOGY_EMBARGO", EventType.TECHNOLOGY_EMBARGO),
        ("TRADE_POLICY_CHANGE", EventType.TRADE_POLICY_CHANGE),
        ("QUOTA_CHANGE", EventType.QUOTA_CHANGE),
    ],
)
def test_all_classifier_labels_map_to_canonical_event_types(
    classifier_label: str,
    expected: EventType,
) -> None:
    assert normalize_classifier_event_type(classifier_label) is expected


def test_historical_aliases_normalize_at_boundary() -> None:
    assert normalize_classifier_event_type("facility_shutdown") is EventType.FACILITY_OUTAGE
    assert normalize_classifier_event_type("regulatory_change") is EventType.REGULATION_CHANGE


def test_event_type_values_match_classifier_taxonomy() -> None:
    assert {event_type.value for event_type in EventType} == {
        "supply_disruption",
        "regulation_change",
        "facility_outage",
        "technology_embargo",
        "trade_policy_change",
        "quota_change",
    }


def test_built_event_persists_canonical_taxonomy_value() -> None:
    event = build_news_event(
        article_id="taxonomy-1",
        classifier_label="TECHNOLOGY_EMBARGO",
        source="test",
        timestamp=datetime.now(timezone.utc),
        confidence=0.9,
        title="Technology exports restricted",
    )
    assert event.event_type is EventType.TECHNOLOGY_EMBARGO
    assert event.event_type.value == "technology_embargo"


def test_unsupported_classifier_label_is_rejected() -> None:
    with pytest.raises(ValueError, match="Unsupported classifier event label"):
        normalize_classifier_event_type("UNKNOWN_CATEGORY")
