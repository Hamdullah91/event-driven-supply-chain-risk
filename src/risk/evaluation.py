from __future__ import annotations

from dataclasses import dataclass

from src.risk.mathematics import RiskPropagationResult, calculate_path_risk
from src.risk.scoring import severity_to_initial_risk


@dataclass(frozen=True, slots=True)
class RiskScenario:
    """Deterministic disruption scenario used to evaluate risk propagation."""

    scenario_id: str
    name: str
    event_type: str
    severity: str
    dependency_weights: tuple[float, float, float]


@dataclass(frozen=True, slots=True)
class RiskScenarioEvaluation:
    """One scenario evaluated at one, two, and three downstream hops."""

    scenario: RiskScenario
    one_hop: RiskPropagationResult
    two_hop: RiskPropagationResult
    three_hop: RiskPropagationResult


DEFAULT_RISK_SCENARIOS: tuple[RiskScenario, ...] = (
    RiskScenario(
        scenario_id="facility-outage",
        name="Facility outage",
        event_type="FACILITY_OUTAGE",
        severity="high",
        dependency_weights=(0.95, 0.85, 0.75),
    ),
    RiskScenario(
        scenario_id="supplier-failure",
        name="Supplier failure",
        event_type="SUPPLY_DISRUPTION",
        severity="high",
        dependency_weights=(0.90, 0.80, 0.70),
    ),
    RiskScenario(
        scenario_id="trade-restriction",
        name="Trade restriction",
        event_type="TRADE_POLICY_CHANGE",
        severity="medium",
        dependency_weights=(0.85, 0.75, 0.65),
    ),
    RiskScenario(
        scenario_id="technology-embargo",
        name="Technology embargo",
        event_type="TECHNOLOGY_EMBARGO",
        severity="critical",
        dependency_weights=(0.95, 0.90, 0.85),
    ),
)


def evaluate_risk_scenario(scenario: RiskScenario) -> RiskScenarioEvaluation:
    """Evaluate a disruption scenario over one-, two-, and three-hop paths."""
    initial_risk = severity_to_initial_risk(scenario.severity)
    weights = scenario.dependency_weights

    return RiskScenarioEvaluation(
        scenario=scenario,
        one_hop=calculate_path_risk(
            initial_risk=initial_risk,
            dependency_weights=weights[:1],
        ),
        two_hop=calculate_path_risk(
            initial_risk=initial_risk,
            dependency_weights=weights[:2],
        ),
        three_hop=calculate_path_risk(
            initial_risk=initial_risk,
            dependency_weights=weights,
        ),
    )


def evaluate_default_risk_scenarios() -> tuple[RiskScenarioEvaluation, ...]:
    """Run the standard Day 44 evaluation suite."""
    return tuple(evaluate_risk_scenario(item) for item in DEFAULT_RISK_SCENARIOS)
