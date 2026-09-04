from src.nlp.entity_resolution.integration import (
    build_provenanced_relationship,
)


relationship = build_provenanced_relationship(
    source_entity="NVIDIA",
    relationship_type="DEPENDS_ON",
    target_entity="TSMC",
    source="SEC_EDGAR",
    source_document="0001045810-25-000023",
    extraction_method="spacy_triplet",
    confidence=0.91,
    filing_date="2025-02-26",
)

print(relationship.model_dump())