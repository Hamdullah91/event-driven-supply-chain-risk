import pytest

from src.risk.aggregation import (
    RiskContribution,
    aggregate_company_risk,
)


def test_three_simultaneous_events_use_probabilistic_union() -> None:
    result = aggregate_company_risk(
        company_id="nvidia",
        contributions=[
            RiskContribution(event_id="event-a", propagated_risk=0.4),
            RiskContribution(event_id="event-b", propagated_risk=0.7),
            RiskContribution(event_id="event-c", propagated_risk=0.3),
        ],
    )

    assert result.company_id == "nvidia"
    assert result.event_count == 3
    assert result.aggregate_risk == pytest.approx(0.874)


def test_single_event_preserves_its_risk() -> None:
    result = aggregate_company_risk(
        company_id="tsmc",
        contributions=[
            RiskContribution(event_id="event-a", propagated_risk=0.42),
        ],
    )

    assert result.aggregate_risk == pytest.approx(0.42)


def test_no_active_events_produce_zero_risk() -> None:
    result = aggregate_company_risk(
        company_id="asml",
        contributions=[],
    )

    assert result.event_count == 0
    assert result.aggregate_risk == pytest.approx(0.0)


def test_certain_event_caps_company_risk_at_one() -> None:
    result = aggregate_company_risk(
        company_id="boeing",
        contributions=[
            RiskContribution(event_id="event-a", propagated_risk=1.0),
            RiskContribution(event_id="event-b", propagated_risk=0.5),
        ],
    )

    assert result.aggregate_risk == pytest.approx(1.0)


@pytest.mark.parametrize("invalid_risk", [-0.01, 1.01])
def test_invalid_propagated_risk_rejected(invalid_risk: float) -> None:
    with pytest.raises(ValueError):
        aggregate_company_risk(
            company_id="nvidia",
            contributions=[
                RiskContribution(
                    event_id="event-a",
                    propagated_risk=invalid_risk,
                )
            ],
        )


def test_duplicate_event_ids_rejected() -> None:
    with pytest.raises(ValueError, match="duplicate event contribution"):
        aggregate_company_risk(
            company_id="nvidia",
            contributions=[
                RiskContribution(event_id="event-a", propagated_risk=0.4),
                RiskContribution(event_id="event-a", propagated_risk=0.2),
            ],
        )


@pytest.mark.parametrize("company_id", ["", "   "])
def test_empty_company_id_rejected(company_id: str) -> None:
    with pytest.raises(ValueError):
        aggregate_company_risk(
            company_id=company_id,
            contributions=[],
        )


@pytest.mark.parametrize("event_id", ["", "   "])
def test_empty_event_id_rejected(event_id: str) -> None:
    with pytest.raises(ValueError):
        aggregate_company_risk(
            company_id="nvidia",
            contributions=[
                RiskContribution(event_id=event_id, propagated_risk=0.2),
            ],
        )
