from dataclasses import dataclass


@dataclass
class ResolvedEntity:
    original_name: str
    normalized_name: str
    canonical_id: str | None
    canonical_name: str | None
    confidence: float
    resolution_method: str