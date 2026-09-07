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
                    f"Invalid JSON on line {line_number}"
                ) from exc

    return records


def main() -> None:
    records = load_jsonl(DATASET_PATH)

    source_counts = Counter(
        str(record.get("source", "")).strip()
        for record in records
    )

    print("=== SOURCE DISTRIBUTION ===")

    for source, count in sorted(source_counts.items()):
        print(f"{source or '<missing>':<20} {count}")

    issues: list[str] = []

    for record in records:
        event_id = str(record.get("id", "<unknown>"))
        source = str(record.get("source", "")).strip().lower()

        if not source:
            issues.append(
                f"{event_id}: missing source"
            )
            continue

        # Real externally sourced records should preserve provenance.
        if source not in {"manual", "synthetic"}:
            if not record.get("source_url"):
                issues.append(
                    f"{event_id}: real source missing source_url"
                )

            if not record.get("published_at"):
                issues.append(
                    f"{event_id}: real source missing published_at"
                )

    print("\n=== PROVENANCE AUDIT ===")

    if issues:
        for issue in issues:
            print(f"WARNING: {issue}")
    else:
        print("PASSED: no provenance issues detected.")

    print(f"\nTotal examples: {len(records)}")


if __name__ == "__main__":
    main()