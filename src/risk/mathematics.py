from __future__ import annotations

from dataclasses import dataclass
from math import prod
from typing import Sequence


DEFAULT_DECAY_FACTOR = 0.70
MAX_PROPAGATION_HOPS = 3


@dataclass(frozen=True, slots=True)
class RiskPropagationResult:
    """Result of deterministic risk propagation along one graph path."""

    initial_risk: float
    dependency_weights: tuple[float, ...]
    hop_distance: int
    path_dependency: float
    decay_factor: float
    distance_decay: float
    propagated_risk: float


def _validate_unit_interval(
    value: float,
    *,
    name: str,
) -> None:
    if not 0.0 <= value <= 1.0:
        raise ValueError(
            f"{name} must be between 0.0 and 1.0 inclusive; "
            f"received {value!r}."
        )


def calculate_distance_decay(
    hop_distance: int,
    *,
    decay_factor: float = DEFAULT_DECAY_FACTOR,
) -> float:
    """
    Calculate distance attenuation for a supply-chain path.

    Formula:
        D(h) = lambda ** (h - 1)

    Therefore:
        hop 1 -> 1.0
        hop 2 -> lambda
        hop 3 -> lambda ** 2
    """
    if not 1 <= hop_distance <= MAX_PROPAGATION_HOPS:
        raise ValueError(
            "hop_distance must be between 1 and "
            f"{MAX_PROPAGATION_HOPS}; received {hop_distance!r}."
        )

    if not 0.0 < decay_factor <= 1.0:
        raise ValueError(
            "decay_factor must be greater than 0.0 and "
            f"less than or equal to 1.0; received {decay_factor!r}."
        )

    return decay_factor ** (hop_distance - 1)


def calculate_path_dependency(
    dependency_weights: Sequence[float],
) -> float:
    """
    Calculate the combined dependency strength of a graph path.

    Formula:
        W(P) = product(w_i)
    """
    if not dependency_weights:
        raise ValueError(
            "dependency_weights must contain at least one weight."
        )

    if len(dependency_weights) > MAX_PROPAGATION_HOPS:
        raise ValueError(
            "dependency_weights cannot contain more than "
            f"{MAX_PROPAGATION_HOPS} weights."
        )

    for index, weight in enumerate(dependency_weights, start=1):
        _validate_unit_interval(
            weight,
            name=f"dependency_weights[{index - 1}]",
        )

    return prod(dependency_weights)


def calculate_path_risk(
    *,
    initial_risk: float,
    dependency_weights: Sequence[float],
    decay_factor: float = DEFAULT_DECAY_FACTOR,
) -> RiskPropagationResult:
    """
    Calculate propagated supply-chain risk along one path.

    Formula:
        R(e, P) =
            R0
            * product(w_i)
            * lambda ** (h - 1)

    Risk propagation is intentionally limited to three hops.
    """
    _validate_unit_interval(
        initial_risk,
        name="initial_risk",
    )

    weights = tuple(dependency_weights)
    hop_distance = len(weights)

    path_dependency = calculate_path_dependency(weights)

    distance_decay = calculate_distance_decay(
        hop_distance,
        decay_factor=decay_factor,
    )

    propagated_risk = (
        initial_risk
        * path_dependency
        * distance_decay
    )

    # Floating-point protection. With valid inputs the result
    # should already be inside [0, 1].
    propagated_risk = min(
        1.0,
        max(0.0, propagated_risk),
    )

    return RiskPropagationResult(
        initial_risk=initial_risk,
        dependency_weights=weights,
        hop_distance=hop_distance,
        path_dependency=path_dependency,
        decay_factor=decay_factor,
        distance_decay=distance_decay,
        propagated_risk=propagated_risk,
    )