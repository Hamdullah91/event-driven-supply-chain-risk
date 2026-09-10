from __future__ import annotations

import logging
from typing import Iterable

from src.nlp.entity_resolution.resolver import resolve_company
from src.nlp.triplet_extractor import GraphCandidate
from src.nlp.validation.relationship_rules import VALID_RELATIONSHIPS
from src.nlp.validation.validator import RelationshipCandidate


logger = logging.getLogger(__name__)


FILING_COMPANY_REFERENCES = {
    "we",
    "us",
    "our",
    "ours",
    "ourselves",
    "company",
    "the company",
}

FACILITY_TERMS = {
    "facility",
    "facilities",
    "plant",
    "plants",
    "factory",
    "factories",
    "fab",
    "fabs",
    "warehouse",
    "warehouses",
    "distribution center",
    "assembly plant",
    "manufacturing facility",
}

MATERIAL_TERMS = {
    "silicon",
    "wafer",
    "wafers",
    "lithium",
    "cobalt",
    "nickel",
    "graphite",
    "copper",
    "aluminum",
    "aluminium",
    "steel",
    "resin",
    "chemicals",
    "gases",
    "raw materials",
}

TECHNOLOGY_TERMS = {
    "ai",
    "ai/ml",
    "artificial intelligence",
    "machine learning",
    "cmos",
    "fpga",
    "fpgas",
    "soc",
    "socs",
    "semiconductor technology",
    "process technology",
}

GENERIC_OBJECTS = {
    "product",
    "products",
    "component",
    "components",
    "system",
    "systems",
    "technology",
    "technologies",
    "material",
    "materials",
    "facility",
    "facilities",
    "supplier",
    "suppliers",
    "vendor",
    "vendors",
    "customer",
    "customers",
    "partner",
    "partners",
    "information",
    "services",
    "service",
    "business",
    "operations",
    "capacity",
}


def _resolve_company_name(
    name: str,
    *,
    filing_company: str,
) -> str | None:
    cleaned_name = name.strip()

    if cleaned_name.lower() in FILING_COMPANY_REFERENCES:
        filing_company_result = resolve_company(filing_company)

        if filing_company_result.canonical_name:
            return filing_company_result.canonical_name

        return filing_company

    resolution = resolve_company(cleaned_name)

    if resolution.canonical_id is None:
        return None

    return resolution.canonical_name


def _infer_non_company_type(
    name: str,
    relationship: str,
) -> str | None:
    """Conservative ontology-aware fallback when spaCy NER has no type."""
    normalized = " ".join(name.strip().lower().split())

    if not normalized or normalized in GENERIC_OBJECTS:
        return None

    if relationship in {"OPERATES", "OWNS"}:
        if any(term in normalized for term in FACILITY_TERMS):
            return "Facility"
        return None

    if relationship == "USES":
        if normalized in MATERIAL_TERMS:
            return "Material"
        if normalized in TECHNOLOGY_TERMS:
            return "Technology"
        return None

    if relationship == "PRODUCES":
        if normalized in MATERIAL_TERMS:
            return "Material"
        return "Product"

    return None


def _resolve_subject(
    candidate: GraphCandidate,
    *,
    filing_company: str,
) -> tuple[str, str] | None:
    """Resolve candidate subject while keeping SEC filing company canonical."""
    cleaned = candidate.subject.strip()

    if cleaned.lower() in FILING_COMPANY_REFERENCES:
        resolved = _resolve_company_name(
            cleaned,
            filing_company=filing_company,
        )
        return (resolved, "Company") if resolved else None

    if candidate.subject_type == "Company":
        resolved = _resolve_company_name(
            cleaned,
            filing_company=filing_company,
        )
        return (resolved, "Company") if resolved else None

    # Most SEC dependency statements use the filing company or a named ORG
    # as subject. Do not promote arbitrary noun phrases into graph entities.
    resolved = _resolve_company_name(
        cleaned,
        filing_company=filing_company,
    )
    if resolved:
        return resolved, "Company"

    return None


def _resolve_object(
    candidate: GraphCandidate,
    *,
    filing_company: str,
) -> tuple[str, str] | None:
    cleaned = candidate.object.strip()
    normalized = " ".join(cleaned.lower().split())

    if candidate.object_type == "Company":
        resolved = _resolve_company_name(
            cleaned,
            filing_company=filing_company,
        )
        return (resolved, "Company") if resolved else None

    # Predicate-aware correction takes precedence over spaCy's entity label.
    # Short technology terms such as "AI" are sometimes mislabeled as GPE/LOC.
    if candidate.predicate == "USES":
        if normalized in MATERIAL_TERMS:
            return cleaned, "Material"
        if normalized in TECHNOLOGY_TERMS:
            return cleaned, "Technology"

    # OPERATES/OWNS are valid only for facilities in the current ontology.
    # A geographic location such as "U.S." must not become an OWNS target.
    if candidate.predicate in {"OPERATES", "OWNS"}:
        if candidate.object_type == "Facility":
            if normalized in GENERIC_OBJECTS:
                return None
            return cleaned, "Facility"
        inferred_type = _infer_non_company_type(
            cleaned,
            candidate.predicate,
        )
        if inferred_type == "Facility":
            return cleaned, "Facility"
        return None

    # Preserve trusted spaCy ontology-compatible types directly. Final
    # predicate/type compatibility is checked in resolve_graph_candidates.
    if candidate.object_type in {
        "Facility",
        "Product",
        "Material",
        "Technology",
        "Location",
    }:
        if normalized in GENERIC_OBJECTS:
            return None
        return cleaned, candidate.object_type

    # An untyped object may still be a known company alias.
    resolved_company = _resolve_company_name(
        cleaned,
        filing_company=filing_company,
    )
    if resolved_company:
        return resolved_company, "Company"

    inferred_type = _infer_non_company_type(
        cleaned,
        candidate.predicate,
    )
    if inferred_type:
        return cleaned, inferred_type

    return None


def resolve_graph_candidates(
    candidates: Iterable[GraphCandidate],
    *,
    filing_company: str,
) -> list[RelationshipCandidate]:
    resolved_candidates: list[RelationshipCandidate] = []

    for candidate in candidates:
        subject = _resolve_subject(
            candidate,
            filing_company=filing_company,
        )

        if subject is None:
            logger.warning(
                "Unresolved subject skipped: %s",
                candidate.subject,
            )
            continue

        object_value = _resolve_object(
            candidate,
            filing_company=filing_company,
        )

        if object_value is None:
            logger.warning(
                "Unresolved object skipped: %s",
                candidate.object,
            )
            continue

        subject_name, subject_type = subject
        object_name, object_type = object_value
        relationship = candidate.predicate

        # Using a named external company for manufacturing/foundry services
        # represents a company dependency. Typed Material/Technology USES
        # relationships remain USES and are validated by the ontology.
        if relationship == "USES" and object_type == "Company":
            relationship = "DEPENDS_ON"

        rule = (subject_type, relationship, object_type)
        if rule not in VALID_RELATIONSHIPS:
            logger.warning(
                "Ontology-incompatible resolved candidate skipped: %s -[%s]-> %s (%s -> %s)",
                subject_name,
                relationship,
                object_name,
                subject_type,
                object_type,
            )
            continue

        resolved_candidates.append(
            RelationshipCandidate(
                subject=subject_name,
                subject_type=subject_type,
                relationship=relationship,
                object=object_name,
                object_type=object_type,
            )
        )

    unique_candidates: list[RelationshipCandidate] = []
    seen = set()

    for candidate in resolved_candidates:
        key = (
            candidate.subject,
            candidate.subject_type,
            candidate.relationship,
            candidate.object,
            candidate.object_type,
        )

        if key in seen:
            continue

        seen.add(key)
        unique_candidates.append(candidate)

    return unique_candidates
