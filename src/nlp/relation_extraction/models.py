from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class RelationCandidate:
    """Evidence-rich relation candidate emitted before entity resolution."""

    subject: str
    relationship: str
    object: str
    source_sentence: str
    pattern_id: str
    voice: str
    subject_type: str | None = None
    object_type: str | None = None
    extraction_confidence: float = 0.0
    attribution_confidence: float = 0.0

    @property
    def confidence(self) -> float:
        """Conservative pre-resolution evidence score."""
        return min(
            self.extraction_confidence,
            self.attribution_confidence,
        )
