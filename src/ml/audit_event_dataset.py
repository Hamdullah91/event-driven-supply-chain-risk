from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]

DEFAULT_DATASET_PATH = (
    PROJECT_ROOT
    / "data"
    / "event_classifier"
    / "raw"
    / "events.jsonl"
)


LABEL_HINT_WORDS = {
    "SUPPLY_DISRUPTION": {
        "shortage",
        "delay",
        "delayed",
        "delivery",
        "supplier",
        "capacity",
        "bottleneck",
        "availability",
    },
    "REGULATION_CHANGE": {
        "regulation",
        "regulations",
        "regulator",
        "regulators",
        "requirements",
        "standards",
        "compliance",
    },
    "FACILITY_OUTAGE": {
        "fire",
        "flood",
        "earthquake",
        "explosion",
        "shutdown",
        "halted",
        "suspended",
        "outage",
    },
    "TECHNOLOGY_EMBARGO": {
        "technology",
        "advanced",
        "export",
        "controls",
        "prohibited",
        "restricted",
        "embargo",
    },
    "TRADE_POLICY_CHANGE": {
        "tariff",
        "tariffs",
        "sanctions",
        "customs",
        "duties",
        "trade",
        "licensing",
    },
    "QUOTA_CHANGE": {
        "quota",
        "quotas",
        "allocation",
        "ceiling",
        "volume",
        "limit",
        "permitted",
    },
}


def get_dataset_path() -> Path:
    if len(sys.argv) > 1:
        return PROJECT_ROOT / sys.argv[1]

    return DEFAULT_DATASET_PATH


def load_records() -> list[dict[str, str]]:
    dataset_path = get_dataset_path()

    records: list[dict[str, str]] = []

    with dataset_path.open("r", encoding="utf-8") as file:
        for line in file:
            line = line.strip()

            if line:
                records.append(json.loads(line))

    print(f"Auditing: {dataset_path}")

    return records


def tokenize(text: str) -> list[str]:
    return re.findall(r"[a-zA-Z]+", text.lower())


def audit_class_balance(records: list[dict[str, str]]) -> None:
    counts = Counter(record["label"] for record in records)

    print("\n=== CLASS BALANCE ===")

    for label, count in sorted(counts.items()):
        print(f"{label:<25} {count}")


def audit_text_lengths(records: list[dict[str, str]]) -> None:
    grouped: dict[str, list[int]] = defaultdict(list)

    for record in records:
        grouped[record["label"]].append(
            len(tokenize(record["text"]))
        )

    print("\n=== TEXT LENGTHS ===")

    for label, lengths in sorted(grouped.items()):
        print(
            f"{label:<25} "
            f"min={min(lengths):>2} "
            f"max={max(lengths):>2} "
            f"avg={mean(lengths):.1f}"
        )


def audit_repeated_words(records: list[dict[str, str]]) -> None:
    grouped_words: dict[str, Counter[str]] = defaultdict(Counter)

    for record in records:
        words = tokenize(record["text"])

        grouped_words[record["label"]].update(words)

    print("\n=== MOST COMMON WORDS BY CLASS ===")

    for label, counter in sorted(grouped_words.items()):
        print(f"\n{label}")

        for word, count in counter.most_common(10):
            print(f"  {word:<18} {count}")


def audit_label_hint_words(records: list[dict[str, str]]) -> None:
    print("\n=== LABEL-HINT WORD FREQUENCY ===")

    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)

    for record in records:
        grouped[record["label"]].append(record)

    for label, examples in sorted(grouped.items()):
        hint_words = LABEL_HINT_WORDS.get(label, set())

        matched_examples = 0

        for example in examples:
            words = set(tokenize(example["text"]))

            if words & hint_words:
                matched_examples += 1

        ratio = matched_examples / len(examples)

        print(
            f"{label:<25} "
            f"{matched_examples}/{len(examples)} "
            f"({ratio:.0%})"
        )


def audit_duplicate_openings(records: list[dict[str, str]]) -> None:
    openings: Counter[str] = Counter()

    for record in records:
        words = tokenize(record["text"])

        opening = " ".join(words[:3])

        if opening:
            openings[opening] += 1

    print("\n=== REPEATED 3-WORD OPENINGS ===")

    found = False

    for opening, count in openings.most_common():
        if count > 1:
            found = True
            print(f"{opening:<40} {count}")

    if not found:
        print("No repeated 3-word openings detected.")


def main() -> None:
    records = load_records()

    print(f"Dataset size: {len(records)}")

    audit_class_balance(records)
    audit_text_lengths(records)
    audit_repeated_words(records)
    audit_label_hint_words(records)
    audit_duplicate_openings(records)


if __name__ == "__main__":
    main()