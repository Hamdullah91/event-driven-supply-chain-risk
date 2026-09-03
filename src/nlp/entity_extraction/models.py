from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ExtractedEntity:
    text: str
    nlp_label: str
    domain_type: str | None
    start_char: int
    end_char: int
    confidence: float | None = None