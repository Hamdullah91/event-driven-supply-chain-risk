import json
from pathlib import Path

from src.nlp.entity_extraction.extractor import EntityExtractor


def main() -> None:
    processed_file = next(
        Path("data/processed/sec").rglob("processed.json")
    )

    data = json.loads(
        processed_file.read_text(encoding="utf-8")
    )

    extractor = EntityExtractor()

    print(f"Company: {data['company_name']}")
    print(f"Filing: {data['accession_number']}")
    print()

    for section in data["sections"]:
        text = section.get("text", "").strip()

        if not text:
            continue

        entities = extractor.extract_long_text(text)

        print(
            f"Item {section['item_number']} - {section['title']}"
        )

        for entity in entities[:30]:
            print(
                f"  {entity.text!r:35} "
                f"NLP={entity.nlp_label:12} "
                f"DOMAIN={entity.domain_type}"
            )

        print(f"  Total entities: {len(entities)}")
        print()


if __name__ == "__main__":
    main()