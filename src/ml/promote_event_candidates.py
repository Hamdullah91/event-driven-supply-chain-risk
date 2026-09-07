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
    / "real_news_candidates.jsonl"
)

DATASET_PATH = (
    PROJECT_ROOT
    / "data"
    / "event_classifier"
    / "raw"
    / "events.jsonl"
)


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    records = []

    with path.open("r", encoding="utf-8") as file:
        for line in file:
            line = line.strip()

            if line:
                records.append(json.loads(line))

    return records


def write_jsonl(
    path: Path,
    records: list[dict[str, Any]],
) -> None:
    with path.open("w", encoding="utf-8") as file:
        for record in records:
            file.write(
                json.dumps(record, ensure_ascii=False) + "\n"
            )


def get_next_event_number(
    records: list[dict[str, Any]],
) -> int:
    numbers = []

    for record in records:
        event_id = str(record["id"])

        if event_id.startswith("evt_"):
            numbers.append(int(event_id.split("_")[1]))

    return max(numbers, default=0) + 1


def main() -> None:
    candidates = load_jsonl(CANDIDATES_PATH)
    existing = load_jsonl(DATASET_PATH)

    existing_text_to_id = {
        str(record["text"]).strip().lower(): record["id"]
        for record in existing
    }

    next_number = get_next_event_number(existing)

    promoted = 0

    with DATASET_PATH.open("a", encoding="utf-8") as dataset_file:
        for candidate in candidates:

            if candidate.get("review_status") != "accepted":
                continue

            text = str(candidate["text"]).strip()
            normalized_text = text.lower()

            # Candidate was already inserted previously.
            if normalized_text in existing_text_to_id:
                existing_id = existing_text_to_id[normalized_text]

                candidate["review_status"] = "promoted"
                candidate["promoted_event_id"] = existing_id

                print(
                    f"{candidate['id']} already exists as "
                    f"{existing_id}"
                )

                continue

            event_id = f"evt_{next_number:06d}"

            record = {
                "id": event_id,
                "text": text,
                "label": candidate["proposed_label"],
                "source": candidate["source"],
                "source_url": candidate.get("source_url"),
                "published_at": candidate.get("published_at"),
            }

            dataset_file.write(
                json.dumps(record, ensure_ascii=False) + "\n"
            )

            existing_text_to_id[normalized_text] = event_id

            candidate["review_status"] = "promoted"
            candidate["promoted_event_id"] = event_id

            print(
                f"{candidate['id']} -> "
                f"{event_id} [{candidate['proposed_label']}]"
            )

            next_number += 1
            promoted += 1

    write_jsonl(CANDIDATES_PATH, candidates)

    print(f"\nNew candidates promoted: {promoted}")


if __name__ == "__main__":
    main()