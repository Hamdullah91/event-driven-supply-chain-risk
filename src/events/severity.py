from __future__ import annotations

from dataclasses import dataclass

from src.events.types import EventSeverity


@dataclass(frozen=True, slots=True)
class SeverityAssessment:
    """Deterministic severity decision with a thesis-explainable reason."""

    severity: EventSeverity
    reason: str
    matched_cue: str | None = None


def _normalize(text: str) -> str:
    return " ".join(text.casefold().replace("-", " ").split())


# These are explicit impact/severity cues, not classifier-confidence thresholds.
# The classifier answers "what event type is this?"; this module answers "how
# severe does the available text say the impact is?".
CRITICAL_CUES = (
    "catastrophic",
    "destroyed",
    "complete shutdown",
    "total shutdown",
    "indefinite shutdown",
    "indefinitely closed",
    "force majeure",
    "nationwide shutdown",
)

# Evaluate explicit low-impact phrases before generic high/medium terms such as
# "shutdown" and "outage" so "brief shutdown" is not accidentally promoted.
LOW_CUES = (
    "minor outage",
    "minor disruption",
    "minor shutdown",
    "brief outage",
    "brief disruption",
    "brief shutdown",
    "temporary shutdown",
    "localized disruption",
    "limited disruption",
    "small delay",
    "short delay",
    "temporary slowdown",
)

HIGH_CUES = (
    "major outage",
    "major disruption",
    "severe shortage",
    "halted production",
    "production halted",
    "plant shutdown",
    "factory shutdown",
    "plant closure",
    "factory closure",
    "export ban",
    "import ban",
    "embargo",
    "shutdown",
)

MEDIUM_CUES = (
    "outage",
    "disruption",
    "shortage",
    "restriction",
    "quota cut",
    "quota reduction",
    "quota reduced",
    "reduced production",
    "production cut",
    "suspended operations",
    "temporary closure",
    "delay",
    "tariff",
    "sanction",
)


def _first_match(text: str, cues: tuple[str, ...]) -> str | None:
    return next((cue for cue in cues if cue in text), None)


def assess_event_severity(*, event_type: str, texts: list[str]) -> SeverityAssessment:
    """Assign categorical event severity from explicit impact language.

    The mapping deliberately does not use classifier confidence. If the available
    text contains no defensible impact cue, UNKNOWN is preserved instead of
    inventing severity.
    """

    text = _normalize("\n".join(part for part in texts if part and part.strip()))
    if not text:
        return SeverityAssessment(
            severity=EventSeverity.UNKNOWN,
            reason="No event context was available for severity assessment.",
        )

    for severity, cues in (
        (EventSeverity.CRITICAL, CRITICAL_CUES),
        (EventSeverity.LOW, LOW_CUES),
        (EventSeverity.HIGH, HIGH_CUES),
        (EventSeverity.MEDIUM, MEDIUM_CUES),
    ):
        cue = _first_match(text, cues)
        if cue is not None:
            return SeverityAssessment(
                severity=severity,
                matched_cue=cue,
                reason=(
                    f"Assigned {severity.value} severity because explicit impact "
                    f"cue {cue!r} was found for classified event type {event_type}."
                ),
            )

    return SeverityAssessment(
        severity=EventSeverity.UNKNOWN,
        reason=(
            "No explicit impact/severity cue was found; UNKNOWN is preserved "
            f"for classified event type {event_type}."
        ),
    )
