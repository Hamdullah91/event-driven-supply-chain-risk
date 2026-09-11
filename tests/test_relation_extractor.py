from __future__ import annotations

import spacy
from spacy.tokens import Doc

from src.nlp.relation_extraction import RelationExtractor


def _nlp(words, heads, deps, pos, lemmas, ents=()):
    nlp = spacy.blank("en")

    def component(_text):
        doc = Doc(
            nlp.vocab,
            words=words,
            heads=heads,
            deps=deps,
            pos=pos,
            lemmas=lemmas,
            sent_starts=[True] + [False] * (len(words) - 1),
        )
        spans = []
        for start, end, label in ents:
            spans.append(doc.char_span(doc[start:end].start_char, doc[start:end].end_char, label=label))
        doc.ents = tuple(span for span in spans if span is not None)
        return doc

    return component


def test_extracts_dependency_from_source_from_company():
    nlp = _nlp(
        ["We", "source", "chips", "from", "TSMC"],
        [1, 1, 1, 1, 3],
        ["nsubj", "ROOT", "dobj", "prep", "pobj"],
        ["PRON", "VERB", "NOUN", "ADP", "PROPN"],
        ["we", "source", "chip", "from", "TSMC"],
        [(4, 5, "ORG")],
    )
    candidates = RelationExtractor(nlp).extract("ignored")
    assert len(candidates) == 1
    assert candidates[0].relationship == "DEPENDS_ON"
    assert candidates[0].subject == "We"
    assert candidates[0].object == "TSMC"
    assert candidates[0].object_type == "Company"


def test_extracts_supply_destination_not_supplied_product():
    nlp = _nlp(
        ["TSMC", "supplies", "chips", "to", "NVIDIA"],
        [1, 1, 1, 1, 3],
        ["nsubj", "ROOT", "dobj", "prep", "pobj"],
        ["PROPN", "VERB", "NOUN", "ADP", "PROPN"],
        ["TSMC", "supply", "chip", "to", "NVIDIA"],
        [(0, 1, "ORG"), (4, 5, "ORG")],
    )
    candidate = RelationExtractor(nlp).extract("ignored")[0]
    assert candidate.relationship == "SUPPLIES"
    assert candidate.subject == "TSMC"
    assert candidate.object == "NVIDIA"


def test_produces_requires_product_object():
    nlp = _nlp(
        ["We", "manufacture", "processors"],
        [1, 1, 1],
        ["nsubj", "ROOT", "dobj"],
        ["PRON", "VERB", "NOUN"],
        ["we", "manufacture", "processor"],
    )
    assert RelationExtractor(nlp).extract("ignored") == []


def test_operates_requires_facility_object():
    nlp = _nlp(
        ["We", "operate", "Fab", "42"],
        [1, 1, 1, 2],
        ["nsubj", "ROOT", "dobj", "nummod"],
        ["PRON", "VERB", "PROPN", "NUM"],
        ["we", "operate", "Fab", "42"],
        [(2, 4, "FAC")],
    )
    candidate = RelationExtractor(nlp).extract("ignored")[0]
    assert candidate.relationship == "OPERATES"
    assert candidate.object_type == "Facility"


def test_does_not_emit_generic_provide_without_destination():
    nlp = _nlp(
        ["We", "provide", "services"],
        [1, 1, 1],
        ["nsubj", "ROOT", "dobj"],
        ["PRON", "VERB", "NOUN"],
        ["we", "provide", "service"],
    )
    assert RelationExtractor(nlp).extract("ignored") == []
