from __future__ import annotations


SEVERITY_RISK_SCORES: dict[str, float] = {
    "unknown": 0.0,
    "low": 0.25,
    "medium": 0.50,
    "high": 0.75,
    "critical": 1.0,
}


def severity_to_initial_risk(severity: str) -> float:
    """Convert the existing categorical Event severity to [0, 1] risk."""

    normalized = severity.strip().lower()

    try:
        return SEVERITY_RISK_SCORES[normalized]
    except KeyError as exc:
        raise ValueError(
            f"Unsupported event severity: {severity!r}."
        ) from exc
