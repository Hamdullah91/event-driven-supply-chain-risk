from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[2]

DATASET_PATH = (
    PROJECT_ROOT
    / "data"
    / "event_classifier"
    / "raw"
    / "events.jsonl"
)

LABEL_MAP_PATH = (
    PROJECT_ROOT
    / "data"
    / "event_classifier"
    / "label_map.json"
)


def load_label_map() -> dict[str, int]:
    with LABEL_MAP_PATH.open("r", encoding="utf-8") as file:
        return json.load(file)


def load_dataset() -> list[dict[str, Any]]:
    records = []

    with DATASET_PATH.open("r", encoding="utf-8") as file:
        for line_number, line in enumerate(file, start=1):
            line = line.strip()

            if not line:
                continue

            try:
                records.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise ValueError(
                    f"Invalid JSON on line {line_number}"
                ) from exc

    return records


def validate_dataset(
    records: list[dict[str, Any]],
    valid_labels: set[str],
) -> None:
    required_fields = {"id", "text", "label"}

    seen_ids: set[str] = set()
    seen_texts: set[str] = set()

    for index, record in enumerate(records, start=1):
        missing = required_fields - record.keys()

        if missing:
            raise ValueError(
                f"Record {index} missing fields: {sorted(missing)}"
            )

        event_id = str(record["id"]).strip()
        text = str(record["text"]).strip()
        label = str(record["label"]).strip()

        if not event_id:
            raise ValueError(f"Record {index} has an empty id.")

        if not text:
            raise ValueError(f"{event_id} has empty text.")

        if label not in valid_labels:
            raise ValueError(
                f"{event_id} has invalid label: {label}"
            )

        if event_id in seen_ids:
            raise ValueError(f"Duplicate id: {event_id}")

        normalized_text = text.lower()

        if normalized_text in seen_texts:
            raise ValueError(
                f"Duplicate text detected: {event_id}"
            )

        seen_ids.add(event_id)
        seen_texts.add(normalized_text)


def print_distribution(
    records: list[dict[str, Any]],
) -> None:
    counts = Counter(record["label"] for record in records)

    print(f"\nTotal examples: {len(records)}")
    print("\nClass distribution:")

    for label, count in sorted(counts.items()):
        print(f"{label:<25} {count}")


def main() -> None:
    label_map = load_label_map()
    records = load_dataset()

    validate_dataset(
        records=records,
        valid_labels=set(label_map.keys()),
    )

    print("Dataset validation PASSED.")

    print_distribution(records)


if __name__ == "__main__":
    main()