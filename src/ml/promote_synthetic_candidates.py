from __future__ import annotations

import json
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[2]

CANDIDATES_PATH = (
    PROJECT_ROOT
    / "data"
    / "event_classifier"
    / "candidates"
    / "synthetic_300.jsonl"
)

DATASET_PATH = (
    PROJECT_ROOT
    / "data"
    / "event_classifier"
    / "raw"
    / "events.jsonl"
)


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []

    with path.open("r", encoding="utf-8") as file:
        for line_number, line in enumerate(file, start=1):
            line = line.strip()

            if not line:
                continue

            try:
                records.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise ValueError(
                    f"Invalid JSON in {path.name} at line {line_number}"
                ) from exc

    return records


def get_next_event_number(
    records: list[dict[str, Any]],
) -> int:
    numbers: list[int] = []

    for record in records:
        event_id = str(record.get("id", ""))

        if event_id.startswith("evt_"):
            try:
                numbers.append(int(event_id.split("_")[1]))
            except ValueError:
                continue

    return max(numbers, default=0) + 1


def main() -> None:
    candidates = load_jsonl(CANDIDATES_PATH)
    existing = load_jsonl(DATASET_PATH)

    existing_texts = {
        str(record["text"]).strip().lower()
        for record in existing
    }

    next_number = get_next_event_number(existing)

    promoted = 0
    duplicates = 0

    with DATASET_PATH.open("a", encoding="utf-8") as file:
        for candidate in candidates:
            text = str(candidate["text"]).strip()
            normalized_text = text.lower()

            if normalized_text in existing_texts:
                print(
                    f"SKIP duplicate: {candidate['id']}"
                )
                duplicates += 1
                continue

            event_id = f"evt_{next_number:06d}"

            record = {
                "id": event_id,
                "text": text,
                "label": candidate["label"],
                "source": "synthetic",
            }

            file.write(
                json.dumps(record, ensure_ascii=False) + "\n"
            )

            existing_texts.add(normalized_text)

            print(
                f"{candidate['id']} -> "
                f"{event_id} [{candidate['label']}]"
            )

            next_number += 1
            promoted += 1

    print("\n=== PROMOTION REPORT ===")
    print(f"Candidates: {len(candidates)}")
    print(f"Promoted:   {promoted}")
    print(f"Duplicates: {duplicates}")


if __name__ == "__main__":
    main()