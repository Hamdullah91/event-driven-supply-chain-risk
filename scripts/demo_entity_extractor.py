from src.nlp.entity_extraction.extractor import EntityExtractor


extractor = EntityExtractor()

text = """
NVIDIA relies on TSMC for semiconductor manufacturing
in Taiwan and uses advanced silicon wafers for GPU production.
"""

entities = extractor.extract(text)

for entity in entities:
    print(
        f"text={entity.text!r}, "
        f"nlp_label={entity.nlp_label!r}, "
        f"domain_type={entity.domain_type!r}"
    )