from __future__ import annotations

from dataclasses import dataclass

from src.risk.mathematics import calculate_distance_decay


CANDIDATE_DECAY_FACTORS = (0.50, 0.60, 0.70, 0.80, 0.90)


@dataclass(frozen=True, slots=True)
class DecayProfile:
    decay_factor: float
    hop_1: float
    hop_2: float
    hop_3: float


def build_decay_profile(decay_factor: float) -> DecayProfile:
    """Return distance-only risk retention across the supported 3 hops."""
    return DecayProfile(
        decay_factor=decay_factor,
        hop_1=calculate_distance_decay(1, decay_factor=decay_factor),
        hop_2=calculate_distance_decay(2, decay_factor=decay_factor),
        hop_3=calculate_distance_decay(3, decay_factor=decay_factor),
    )


def evaluate_candidates() -> list[DecayProfile]:
    """Evaluate the candidate lambda values used for Day 42 sensitivity analysis."""
    return [
        build_decay_profile(decay_factor)
        for decay_factor in CANDIDATE_DECAY_FACTORS
    ]


def main() -> None:
    print("=== DAY 42 DISTANCE-DECAY SENSITIVITY ===")
    print("Formula: D(h) = lambda ** (h - 1)")
    print()
    print("lambda | hop 1 | hop 2 | hop 3")
    print("-------+-------+-------+------")

    for profile in evaluate_candidates():
        print(
            f"{profile.decay_factor:>6.2f} | "
            f"{profile.hop_1:>5.2f} | "
            f"{profile.hop_2:>5.2f} | "
            f"{profile.hop_3:>5.2f}"
        )

    print()
    print(
        "Selected baseline: lambda = 0.70. "
        "It preserves full direct exposure, retains 70% at hop 2, "
        "and 49% at hop 3 before dependency weights are applied."
    )
    print(
        "This is a transparent calibration baseline, not a learned parameter. "
        "It should be re-evaluated against Day 44 disruption scenarios."
    )


if __name__ == "__main__":
    main()
