from __future__ import annotations

import spacy

from src.graph.ingestion.resolution import resolve_graph_candidates
from src.nlp.relation_extraction import RelationExtractor
from src.nlp.triplet_extractor import GraphCandidate


def _resolved(text: str, filing_company: str):
    nlp = spacy.load("en_core_web_sm")
    extractor = RelationExtractor(nlp)
    raw = [
        GraphCandidate(
            subject=candidate.subject,
            predicate=candidate.relationship,
            object=candidate.object,
            source_sentence=candidate.source_sentence,
            subject_type=candidate.subject_type,
            object_type=candidate.object_type,
        )
        for candidate in extractor.extract(text)
    ]
    return resolve_graph_candidates(raw, filing_company=filing_company)


def _keys(candidates):
    return {
        (
            candidate.subject,
            candidate.relationship,
            candidate.object,
            candidate.object_type,
        )
        for candidate in candidates
    }


def test_recovers_coordinated_foundry_dependency() -> None:
    candidates = _resolved(
        "Moreover, we rely on TSMC, UMC and our other foundries to produce wafers for our IC products.",
        "Advanced Micro Devices, Inc.",
    )
    keys = _keys(candidates)
    assert (
        "Advanced Micro Devices",
        "DEPENDS_ON",
        "Taiwan Semiconductor Manufacturing Company",
        "Company",
    ) in keys
    assert (
        "Advanced Micro Devices",
        "DEPENDS_ON",
        "United Microelectronics Corporation",
        "Company",
    ) in keys


def test_recovers_inherited_subject_production() -> None:
    candidates = _resolved(
        "At this site we use brines extracted from the salar to produce potassium chloride, lithium sulfate, and lithium chloride solutions.",
        "SQM",
    )
    keys = _keys(candidates)
    assert any(
        subject == "SQM" and relationship == "PRODUCES" and object_type == "Product"
        for subject, relationship, _object, object_type in keys
    )


def test_recovers_nominal_owned_product_manufacture() -> None:
    candidates = _resolved(
        "We will need to maintain and significantly grow our access to battery cells, including through the development and manufacture of our own cells, and control our related costs.",
        "Tesla, Inc.",
    )
    assert any(
        candidate.subject == "Tesla"
        and candidate.relationship == "PRODUCES"
        and candidate.object_type == "Product"
        and "cells" in candidate.object.lower()
        for candidate in candidates
    )


def test_recovers_facility_ownership_through_interest() -> None:
    candidates = _resolved(
        "Through our Windfield joint venture, we own a 49% interest in the Greenbushes mine.",
        "Albemarle Corporation",
    )
    assert any(
        candidate.subject == "Albemarle"
        and candidate.relationship == "OWNS"
        and candidate.object_type == "Facility"
        and "Greenbushes mine" in candidate.object
        for candidate in candidates
    )
