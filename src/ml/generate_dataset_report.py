from __future__ import annotations

import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[2]

DATASET_PATH = (
    PROJECT_ROOT
    / "data"
    / "event_classifier"
    / "raw"
    / "events.jsonl"
)

REPORT_PATH = (
    PROJECT_ROOT
    / "data"
    / "event_classifier"
    / "dataset_report.json"
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
                    f"Invalid JSON at line {line_number}"
                ) from exc

    return records


def word_count(text: str) -> int:
    return len(re.findall(r"\b\w+\b", text))


def main() -> None:
    records = load_jsonl(DATASET_PATH)

    label_counts = Counter(
        str(record["label"])
        for record in records
    )

    source_counts = Counter(
        str(record["source"])
        for record in records
    )

    lengths = [
        word_count(str(record["text"]))
        for record in records
    ]

    unique_ids = {
        str(record["id"])
        for record in records
    }

    unique_texts = {
        str(record["text"]).strip().lower()
        for record in records
    }

    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "dataset": str(DATASET_PATH.relative_to(PROJECT_ROOT)),
        "total_examples": len(records),
        "class_distribution": dict(sorted(label_counts.items())),
        "source_distribution": dict(sorted(source_counts.items())),
        "text_length_words": {
            "minimum": min(lengths),
            "maximum": max(lengths),
            "average": round(mean(lengths), 2),
        },
        "integrity": {
            "unique_ids": len(unique_ids),
            "unique_texts": len(unique_texts),
            "duplicate_ids": len(records) - len(unique_ids),
            "duplicate_texts": len(records) - len(unique_texts),
        },
        "day_27_status": "complete",
    }

    REPORT_PATH.write_text(
        json.dumps(report, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print("=== DATASET REPORT ===")
    print(f"Total examples: {len(records)}")
    print(f"Unique IDs:     {len(unique_ids)}")
    print(f"Unique texts:   {len(unique_texts)}")
    print(f"Report written: {REPORT_PATH}")


if __name__ == "__main__":
    main()