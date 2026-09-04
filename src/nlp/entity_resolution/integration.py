from typing import Iterable

from .models import ResolvedEntity
from .resolver import resolve_companies


def resolve_extracted_companies(
    company_names: Iterable[str],
) -> list[ResolvedEntity]:
    """
    Resolve company names produced by the NLP entity extractor.

    Duplicate raw names are removed before resolution.
    """
    unique_names = list(dict.fromkeys(company_names))

    return resolve_companies(unique_names)

def get_resolution_stats(
    results: list[ResolvedEntity],
) -> dict[str, int | float]:
    total = len(results)

    resolved = sum(
        1 for result in results
        if result.canonical_id is not None
    )

    unresolved = total - resolved

    resolution_rate = resolved / total if total else 0.0

    return {
        "total": total,
        "resolved": resolved,
        "unresolved": unresolved,
        "resolution_rate": resolution_rate,
    }