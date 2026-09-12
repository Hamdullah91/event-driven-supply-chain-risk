from __future__ import annotations

import pytest

from src.risk.evaluation import (
    DEFAULT_RISK_SCENARIOS,
    evaluate_default_risk_scenarios,
    evaluate_risk_scenario,
)


EXPECTED_THREE_HOP_RISK = {
    "facility-outage": 0.2225671875,
    "supplier-failure": 0.18522,
    "trade-restriction": 0.101521875,
    "technology-embargo": 0.3561075,
}


def test_day44_contains_all_required_scenarios() -> None:
    assert {scenario.scenario_id for scenario in DEFAULT_RISK_SCENARIOS} == {
        "facility-outage",
        "supplier-failure",
        "trade-restriction",
        "technology-embargo",
    }


def test_day44_scenarios_use_expected_event_taxonomy() -> None:
    event_types = {scenario.event_type for scenario in DEFAULT_RISK_SCENARIOS}

    assert event_types == {
        "FACILITY_OUTAGE",
        "SUPPLY_DISRUPTION",
        "TRADE_POLICY_CHANGE",
        "TECHNOLOGY_EMBARGO",
    }


@pytest.mark.parametrize("scenario", DEFAULT_RISK_SCENARIOS)
def test_risk_decreases_across_hops_for_each_scenario(scenario) -> None:
    evaluation = evaluate_risk_scenario(scenario)

    assert evaluation.one_hop.hop_distance == 1
    assert evaluation.two_hop.hop_distance == 2
    assert evaluation.three_hop.hop_distance == 3

    assert evaluation.one_hop.distance_decay == pytest.approx(1.0)
    assert evaluation.two_hop.distance_decay == pytest.approx(0.70)
    assert evaluation.three_hop.distance_decay == pytest.approx(0.49)

    assert evaluation.one_hop.propagated_risk > evaluation.two_hop.propagated_risk
    assert evaluation.two_hop.propagated_risk > evaluation.three_hop.propagated_risk


@pytest.mark.parametrize("scenario", DEFAULT_RISK_SCENARIOS)
def test_three_hop_scenario_results_match_expected_formula(scenario) -> None:
    evaluation = evaluate_risk_scenario(scenario)

    assert evaluation.three_hop.propagated_risk == pytest.approx(
        EXPECTED_THREE_HOP_RISK[scenario.scenario_id]
    )


@pytest.mark.parametrize("scenario", DEFAULT_RISK_SCENARIOS)
def test_scenario_risk_is_bounded_and_dependency_aware(scenario) -> None:
    evaluation = evaluate_risk_scenario(scenario)

    for result in (
        evaluation.one_hop,
        evaluation.two_hop,
        evaluation.three_hop,
    ):
        assert 0.0 <= result.propagated_risk <= 1.0
        assert 0.0 <= result.path_dependency <= 1.0

    assert evaluation.three_hop.path_dependency == pytest.approx(
        scenario.dependency_weights[0]
        * scenario.dependency_weights[1]
        * scenario.dependency_weights[2]
    )


def test_technology_embargo_has_highest_three_hop_exposure() -> None:
    evaluations = evaluate_default_risk_scenarios()
    highest = max(evaluations, key=lambda item: item.three_hop.propagated_risk)

    assert highest.scenario.scenario_id == "technology-embargo"


def test_default_scenario_suite_is_deterministic() -> None:
    first = evaluate_default_risk_scenarios()
    second = evaluate_default_risk_scenarios()

    assert first == second
