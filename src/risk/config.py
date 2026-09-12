from __future__ import annotations

from dataclasses import dataclass

from src.risk.mathematics import DEFAULT_DECAY_FACTOR, MAX_PROPAGATION_HOPS


@dataclass(frozen=True, slots=True)
class RiskPropagationConfig:
    """Configuration for deterministic multi-hop risk propagation."""

    max_hops: int = MAX_PROPAGATION_HOPS
    decay_factor: float = DEFAULT_DECAY_FACTOR

    def __post_init__(self) -> None:
        if not 1 <= self.max_hops <= MAX_PROPAGATION_HOPS:
            raise ValueError(
                "max_hops must be between 1 and "
                f"{MAX_PROPAGATION_HOPS}; received {self.max_hops!r}."
            )

        if not 0.0 < self.decay_factor <= 1.0:
            raise ValueError(
                "decay_factor must be greater than 0.0 and "
                f"less than or equal to 1.0; received {self.decay_factor!r}."
            )
