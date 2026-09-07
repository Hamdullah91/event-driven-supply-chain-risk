from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]

DEFAULT_PATH = (
    PROJECT_ROOT
    / "data"
    / "event_classifier"
    / "candidates"
    / "synthetic_300.jsonl"
)


CROSS_CLASS_TERMS = {
    "SUPPLY_DISRUPTION": {
        "shutdown", "closed", "halted", "fire",
        "flood", "outage", "plant", "facility",
    },
    "FACILITY_OUTAGE": {
        "supplier", "shortage", "delivery", "deliveries",
        "shipment", "shipments", "supply", "backlog",
    },
    "REGULATION_CHANGE": {
        "export", "import", "border", "customs",
        "tariff", "sanctions", "overseas", "foreign",
    },
    "TRADE_POLICY_CHANGE": {
        "technology", "software", "equipment", "know-how",
        "design", "process", "technical", "advanced",
        "tonnes", "volume", "ceiling", "maximum",
    },
    "TECHNOLOGY_EMBARGO": {
        "tariff", "customs", "border", "duty",
        "duties", "trade", "tonnes", "volume",
    },
    "QUOTA_CHANGE": {
        "license", "licensing", "customs", "tariff",
        "sanctions", "technology", "equipment",
    },
}


def load_jsonl(path: Path) -> list[dict[str, str]]:
    records = []

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


def find_matches(
    text: str,
    terms: set[str],
) -> list[str]:
    lowered = text.lower()

    return sorted(
        term
        for term in terms
        if term in lowered
    )


def main() -> None:
    path = (
        PROJECT_ROOT / sys.argv[1]
        if len(sys.argv) > 1
        else DEFAULT_PATH
    )

    records = load_jsonl(path)

    suspicious: dict[str, list[tuple[dict[str, str], list[str]]]] = (
        defaultdict(list)
    )

    for record in records:
        label = record["label"]

        matches = find_matches(
            record["text"],
            CROSS_CLASS_TERMS.get(label, set()),
        )

        if matches:
            suspicious[label].append(
                (record, matches)
            )

    print(f"Dataset: {path}")
    print(f"Total records: {len(records)}")

    total_flagged = sum(
        len(items)
        for items in suspicious.values()
    )

    print(f"Boundary candidates: {total_flagged}")

    for label in sorted(suspicious):
        print(f"\n=== {label} ===")

        for record, matches in suspicious[label]:
            print(f"\n{record['id']}")
            print(f"Matched: {', '.join(matches)}")
            print(record["text"])


if __name__ == "__main__":
    main()
    