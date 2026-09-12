from __future__ import annotations

from dataclasses import dataclass

from src.risk.mathematics import calculate_distance_decay, calculate_path_risk


CANDIDATE_DECAY_FACTORS = (0.50, 0.60, 0.70, 0.75, 0.80, 0.90)
EXPERIMENT_INITIAL_RISK = 0.90
EXPERIMENT_WEIGHTS = (0.90, 0.80, 0.60)


@dataclass(frozen=True, slots=True)
class DecayProfile:
    decay_factor: float
    hop_1: float
    hop_2: float
    hop_3: float
    hop_1_risk: float
    hop_2_risk: float
    hop_3_risk: float


def build_decay_profile(decay_factor: float) -> DecayProfile:
    """Return distance retention and path risk across the supported 3 hops."""
    hop_1_result = calculate_path_risk(
        initial_risk=EXPERIMENT_INITIAL_RISK,
        dependency_weights=EXPERIMENT_WEIGHTS[:1],
        decay_factor=decay_factor,
    )
    hop_2_result = calculate_path_risk(
        initial_risk=EXPERIMENT_INITIAL_RISK,
        dependency_weights=EXPERIMENT_WEIGHTS[:2],
        decay_factor=decay_factor,
    )
    hop_3_result = calculate_path_risk(
        initial_risk=EXPERIMENT_INITIAL_RISK,
        dependency_weights=EXPERIMENT_WEIGHTS,
        decay_factor=decay_factor,
    )

    return DecayProfile(
        decay_factor=decay_factor,
        hop_1=calculate_distance_decay(1, decay_factor=decay_factor),
        hop_2=calculate_distance_decay(2, decay_factor=decay_factor),
        hop_3=calculate_distance_decay(3, decay_factor=decay_factor),
        hop_1_risk=hop_1_result.propagated_risk,
        hop_2_risk=hop_2_result.propagated_risk,
        hop_3_risk=hop_3_result.propagated_risk,
    )


def evaluate_candidates() -> list[DecayProfile]:
    """Evaluate candidate lambda values used for Day 42 sensitivity analysis."""
    return [
        build_decay_profile(decay_factor)
        for decay_factor in CANDIDATE_DECAY_FACTORS
    ]


def main() -> None:
    print("=== DAY 42 DISTANCE-DECAY SENSITIVITY ===")
    print("Formula: D(h) = lambda ** (h - 1)")
    print(
        "Scenario: initial risk=0.90, dependency weights="
        f"{EXPERIMENT_WEIGHTS}"
    )
    print()
    print("lambda | D1   | D2   | D3   | risk h1 | risk h2 | risk h3")
    print("-------+------+------+------+---------+---------+--------")

    for profile in evaluate_candidates():
        print(
            f"{profile.decay_factor:>6.2f} | "
            f"{profile.hop_1:>4.2f} | "
            f"{profile.hop_2:>4.2f} | "
            f"{profile.hop_3:>4.2f} | "
            f"{profile.hop_1_risk:>7.4f} | "
            f"{profile.hop_2_risk:>7.4f} | "
            f"{profile.hop_3_risk:>7.4f}"
        )

    print()
    print(
        "Selected provisional baseline: lambda = 0.70. "
        "Hop 1 receives no extra distance penalty; hop 2 retains 70% "
        "and hop 3 retains 49% before dependency weights are applied."
    )
    print(
        "This is a calibration baseline, not a learned parameter. "
        "Day 44 scenario evaluation should compare downstream rankings "
        "and decide whether lambda should be revised."
    )


if __name__ == "__main__":
    main()
