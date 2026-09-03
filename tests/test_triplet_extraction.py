import spacy

from src.nlp.triplet_extractor import TripletExtractor


def test_triplet_extraction():
    nlp = spacy.load("en_core_web_sm")
    extractor = TripletExtractor(nlp)

    candidates = extractor.extract(
        "TSMC provides chips to NVIDIA. "
        "Tesla uses lithium. "
        "Intel produces processors."
    )

    results = {
        (c.subject, c.predicate, c.object)
        for c in candidates
    }

    assert ("TSMC", "SUPPLIES", "NVIDIA") in results
    assert ("Tesla", "USES", "lithium") in results
    assert ("Intel", "PRODUCES", "processors") in results


def test_duplicate_candidates_removed():
    nlp = spacy.load("en_core_web_sm")
    extractor = TripletExtractor(nlp)

    candidates = extractor.extract(
        "TSMC provides chips to NVIDIA."
    )

    matches = [
        c
        for c in candidates
        if c.subject == "TSMC"
        and c.predicate == "SUPPLIES"
        and c.object == "NVIDIA"
    ]

    assert len(matches) == 1