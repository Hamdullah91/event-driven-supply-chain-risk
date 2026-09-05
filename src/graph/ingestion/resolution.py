from __future__ import annotations

import logging
from typing import Iterable

from src.nlp.entity_resolution.resolver import resolve_company
from src.nlp.triplet_extractor import GraphCandidate
from src.nlp.validation.validator import RelationshipCandidate


logger = logging.getLogger(__name__)


FILING_COMPANY_REFERENCES = {
    "we",
    "us",
    "our",
    "ours",
    "ourselves",
}


def _resolve_entity(
    name: str,
    *,
    filing_company: str,
) -> str | None:
    """
    Resolve an extracted entity to a canonical company name.

    First-person references in SEC filings refer to the filing company.
    """

    cleaned_name = name.strip()

    if cleaned_name.lower() in FILING_COMPANY_REFERENCES:
        filing_company_result = resolve_company(
            filing_company
        )

        if filing_company_result.canonical_name:
            return filing_company_result.canonical_name

        # Metadata itself is trusted even if not present
        # in the alias dictionary.
        return filing_company

    resolution = resolve_company(cleaned_name)

    if resolution.canonical_id is None:
        return None

    return resolution.canonical_name


def resolve_graph_candidates(
    candidates: Iterable[GraphCandidate],
    *,
    filing_company: str,
) -> list[RelationshipCandidate]:

    resolved_candidates: list[RelationshipCandidate] = []

    for candidate in candidates:

        subject = _resolve_entity(
            candidate.subject,
            filing_company=filing_company,
        )

        if subject is None:
            logger.warning(
                "Unresolved subject skipped: %s",
                candidate.subject,
            )
            continue

        object_name = _resolve_entity(
            candidate.object,
            filing_company=filing_company,
        )

        if object_name is None:
            logger.warning(
                "Unresolved object skipped: %s",
                candidate.object,
            )
            continue
        relationship = candidate.predicate

        if relationship == "USES":
            relationship = "DEPENDS_ON"

        resolved_candidates.append(
            RelationshipCandidate(
                subject=subject,
                subject_type="Company",
                relationship=relationship,
                object=object_name,
                object_type="Company",
            )
        )

    unique_candidates = []
    seen = set()

    for candidate in resolved_candidates:
        key = (
            candidate.subject,
            candidate.relationship,
            candidate.object,
        )

        if key in seen:
            continue

        seen.add(key)
        unique_candidates.append(candidate)

    return unique_candidates