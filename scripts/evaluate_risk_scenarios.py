from __future__ import annotations

from src.risk.evaluation import evaluate_default_risk_scenarios


def main() -> None:
    print("=== DAY 44 RISK ENGINE EVALUATION ===")

    for evaluation in evaluate_default_risk_scenarios():
        scenario = evaluation.scenario
        print(f"\nScenario: {scenario.name}")
        print(f"Event type: {scenario.event_type}")
        print(f"Severity: {scenario.severity}")
        print(f"Dependency weights: {scenario.dependency_weights}")
        print(
            "1-hop risk: "
            f"{evaluation.one_hop.propagated_risk:.6f} "
            f"(decay={evaluation.one_hop.distance_decay:.2f})"
        )
        print(
            "2-hop risk: "
            f"{evaluation.two_hop.propagated_risk:.6f} "
            f"(decay={evaluation.two_hop.distance_decay:.2f})"
        )
        print(
            "3-hop risk: "
            f"{evaluation.three_hop.propagated_risk:.6f} "
            f"(decay={evaluation.three_hop.distance_decay:.2f})"
        )


if __name__ == "__main__":
    main()
