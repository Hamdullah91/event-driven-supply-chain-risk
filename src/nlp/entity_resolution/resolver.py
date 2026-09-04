from rapidfuzz import fuzz, process

from .aliases import COMPANY_ALIASES
from .canonical_entities import CANONICAL_COMPANIES
from .models import ResolvedEntity
from .normalizer import normalize_entity_name


FUZZY_THRESHOLD = 85.0


def resolve_company(name: str) -> ResolvedEntity:
    normalized_name = normalize_entity_name(name)

    # 1. Exact alias match
    canonical_id = COMPANY_ALIASES.get(normalized_name)

    if canonical_id:
        canonical_name = CANONICAL_COMPANIES[canonical_id]["name"]

        return ResolvedEntity(
            original_name=name,
            normalized_name=normalized_name,
            canonical_id=canonical_id,
            canonical_name=canonical_name,
            confidence=1.0,
            resolution_method="alias_exact",
        )

    # 2. Fuzzy alias match
    fuzzy_match = process.extractOne(
        normalized_name,
        COMPANY_ALIASES.keys(),
        scorer=fuzz.ratio,
    )

    if fuzzy_match:
        matched_alias, score, _ = fuzzy_match

        if score >= FUZZY_THRESHOLD:
            canonical_id = COMPANY_ALIASES[matched_alias]
            canonical_name = CANONICAL_COMPANIES[canonical_id]["name"]

            return ResolvedEntity(
                original_name=name,
                normalized_name=normalized_name,
                canonical_id=canonical_id,
                canonical_name=canonical_name,
                confidence=score / 100.0,
                resolution_method="alias_fuzzy",
            )

    # 3. Unresolved
    return ResolvedEntity(
        original_name=name,
        normalized_name=normalized_name,
        canonical_id=None,
        canonical_name=None,
        confidence=0.0,
        resolution_method="unresolved",
    )

def resolve_companies(names: list[str]) -> list[ResolvedEntity]:
    """
    Resolve multiple extracted company names.

    Args:
        names: Raw company names extracted from text.

    Returns:
        Resolution result for every input company.
    """
    return [resolve_company(name) for name in names]