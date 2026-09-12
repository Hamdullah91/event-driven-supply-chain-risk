from __future__ import annotations

from dataclasses import dataclass
from math import prod
from typing import Sequence


@dataclass(frozen=True, slots=True)
class RiskContribution:
    """Propagated risk contributed by one event to one company."""

    event_id: str
    propagated_risk: float


@dataclass(frozen=True, slots=True)
class CompanyRiskAggregation:
    """Bounded company-level risk aggregated from active events."""

    company_id: str
    event_count: int
    contributions: tuple[RiskContribution, ...]
    aggregate_risk: float


def _validate_contribution(contribution: RiskContribution) -> None:
    if not contribution.event_id.strip():
        raise ValueError("event_id must not be empty.")

    if not 0.0 <= contribution.propagated_risk <= 1.0:
        raise ValueError(
            "propagated_risk must be between 0.0 and 1.0 inclusive; "
            f"received {contribution.propagated_risk!r}."
        )


def aggregate_company_risk(
    *,
    company_id: str,
    contributions: Sequence[RiskContribution],
) -> CompanyRiskAggregation:
    """
    Aggregate simultaneous event risk for one company.

    Independent-event union formula:

        R_company = 1 - product(1 - r_i)

    where each ``r_i`` is the already-propagated risk contribution from
    one active event after dependency weighting and distance decay.

    This keeps the final company score bounded in [0, 1] while allowing
    every event to increase exposure without naive additive saturation.
    """
    if not company_id.strip():
        raise ValueError("company_id must not be empty.")

    items = tuple(contributions)
    seen_event_ids: set[str] = set()

    for contribution in items:
        _validate_contribution(contribution)

        if contribution.event_id in seen_event_ids:
            raise ValueError(
                "duplicate event contribution detected for "
                f"event_id={contribution.event_id!r}."
            )
        seen_event_ids.add(contribution.event_id)

    if not items:
        aggregate_risk = 0.0
    else:
        residual_safe_probability = prod(
            1.0 - contribution.propagated_risk
            for contribution in items
        )
        aggregate_risk = 1.0 - residual_safe_probability

    # Floating-point protection.
    aggregate_risk = min(1.0, max(0.0, aggregate_risk))

    return CompanyRiskAggregation(
        company_id=company_id,
        event_count=len(items),
        contributions=items,
        aggregate_risk=aggregate_risk,
    )
