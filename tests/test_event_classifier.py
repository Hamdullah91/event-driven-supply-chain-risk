import pytest

from src.ml.event_classifier import (
    ClassificationResult,
    EventClassifier,
)


MODEL_PATH = "models/event_classifier/distilbert_supply_chain"


def test_classification_result_fields() -> None:
    result = ClassificationResult(
        event_type="FACILITY_OUTAGE",
        confidence=0.80,
        requires_review=False,
        second_event_type="SUPPLY_DISRUPTION",
        second_confidence=0.15,
        confidence_margin=0.65,
    )

    assert result.event_type == "FACILITY_OUTAGE"
    assert result.confidence == pytest.approx(0.80)
    assert result.requires_review is False
    assert result.second_event_type == "SUPPLY_DISRUPTION"
    assert result.second_confidence == pytest.approx(0.15)
    assert result.confidence_margin == pytest.approx(0.65)


def test_empty_article_rejected() -> None:
    classifier = EventClassifier(
        model_path=MODEL_PATH
    )

    with pytest.raises(ValueError):
        classifier.classify("")


def test_classifier_returns_valid_prediction() -> None:
    classifier = EventClassifier(
        model_path=MODEL_PATH
    )

    result = classifier.classify(
        "A fire shut down production at a semiconductor fabrication plant."
    )

    assert isinstance(result.event_type, str)
    assert 0.0 <= result.confidence <= 1.0
    assert isinstance(result.second_event_type, str)
    assert 0.0 <= result.second_confidence <= 1.0
    assert result.confidence_margin >= 0.0
    assert result.confidence >= result.second_confidence