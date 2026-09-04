import json
from pathlib import Path

from src.nlp.entity_resolution.integration import (
    get_resolution_stats,
    resolve_extracted_companies,
)


ENTITY_FILE = Path(
    "data/processed/sec/1045810/"
    "0001045810-26-000021/entities.json"
)


def load_company_names(path: Path) -> list[str]:
    with path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    names: list[str] = []

    sections = data.get("sections", [])

    for section_data in sections:
        entities = section_data.get("entities", [])

        for entity in entities:
            if entity.get("domain_type") == "Company":
                name = entity.get("text")

                if name:
                    names.append(name)

    return names

def main() -> None:
    company_names = load_company_names(ENTITY_FILE)

    results = resolve_extracted_companies(company_names)
    stats = get_resolution_stats(results)

    print()
    print("=== ENTITY RESOLUTION AUDIT ===")
    print(f"Total: {stats['total']}")
    print(f"Resolved: {stats['resolved']}")
    print(f"Unresolved: {stats['unresolved']}")
    print(f"Resolution rate: {stats['resolution_rate']:.2%}")

    print()
    print("=== UNRESOLVED COMPANIES ===")

    for result in results:
        if result.canonical_id is None:
            print(result.original_name)


if __name__ == "__main__":
    main()