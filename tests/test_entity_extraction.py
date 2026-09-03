import pytest

from src.nlp.entity_extraction.extractor import EntityExtractor


@pytest.fixture(scope="module")
def extractor():
    return EntityExtractor()


def test_entity_extraction(extractor):
    text = (
        "NVIDIA relies on TSMC for semiconductor manufacturing "
        "in Taiwan and uses advanced silicon wafers for GPU production."
    )

    entities = extractor.extract(text)

    results = {
        (entity.text, entity.domain_type)
        for entity in entities
    }

    assert ("NVIDIA", "Company") in results
    assert ("TSMC", "Company") in results
    assert ("semiconductor", "Product") in results
    assert ("Taiwan", "Location") in results
    assert ("silicon wafers", "Material") in results
    assert ("GPU", "Product") in results


def test_domain_type_does_not_trust_spacy_label(extractor):
    entities = extractor.extract(
        "AI technology is used for GPU production."
    )

    ai = next(
        entity
        for entity in entities
        if entity.text == "AI"
    )

    gpu = next(
        entity
        for entity in entities
        if entity.text == "GPU"
    )

    assert ai.domain_type is None
    assert gpu.nlp_label == "ORG"
    assert gpu.domain_type == "Product"


def test_empty_text_returns_empty_list(extractor):
    assert extractor.extract("") == []
    assert extractor.extract("   ") == []


def test_longest_domain_match_wins(extractor):
    entities = extractor.extract(
        "The company uses silicon wafers for production."
    )

    texts = [
        entity.text.lower()
        for entity in entities
    ]

    assert "silicon wafers" in texts
    assert "silicon" not in texts


def test_seed_backed_location_validation(extractor):
    entities = extractor.extract(
        "The company operates in Taiwan."
    )

    taiwan = next(
        entity
        for entity in entities
        if entity.text == "Taiwan"
    )

    assert taiwan.domain_type == "Location"