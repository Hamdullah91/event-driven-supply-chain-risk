import json
from dataclasses import asdict
from pathlib import Path

from src.nlp.entity_extraction.extractor import EntityExtractor


def main() -> None:
    extractor = EntityExtractor()

    processed_files = list(
        Path("data/processed/sec").rglob("processed.json")
    )

    for processed_file in processed_files:
        data = json.loads(
            processed_file.read_text(encoding="utf-8")
        )

        output_sections = []

        for section in data.get("sections", []):
            text = section.get("text", "").strip()

            if not text:
                continue

            entities = extractor.extract_long_text(text)

            output_sections.append(
                {
                    "item_number": section.get("item_number"),
                    "title": section.get("title"),
                    "entities": [
                        asdict(entity)
                        for entity in entities
                    ],
                }
            )

        output = {
            "cik": data.get("cik"),
            "company_name": data.get("company_name"),
            "accession_number": data.get("accession_number"),
            "filing_date": data.get("filing_date"),
            "form_type": data.get("form_type"),
            "source_url": data.get("source_url"),
            "sections": output_sections,
        }

        output_file = processed_file.parent / "entities.json"

        output_file.write_text(
            json.dumps(
                output,
                indent=2,
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

        print(f"Created: {output_file}")


if __name__ == "__main__":
    main()