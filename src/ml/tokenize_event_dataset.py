from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from datasets import Dataset, DatasetDict
from sklearn.model_selection import train_test_split
from transformers import AutoTokenizer


PROJECT_ROOT = Path(__file__).resolve().parents[2]

DATA_DIR = PROJECT_ROOT / "data" / "event_classifier"

INPUT_FILE = DATA_DIR / "raw" / "events.jsonl"
LABEL_MAP_FILE = DATA_DIR / "label_map.json"
OUTPUT_DIR = DATA_DIR / "processed"

MODEL_NAME = "distilbert-base-uncased"

RANDOM_SEED = 42
MAX_LENGTH = 256


def load_jsonl(path: Path) -> list[dict]:
    records = []

    with path.open("r", encoding="utf-8") as file:
        for line in file:
            line = line.strip()

            if not line:
                continue

            records.append(json.loads(line))

    return records


def load_label_map(path: Path) -> dict[str, int]:
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def prepare_records(
    records: list[dict],
    label_map: dict[str, int],
) -> list[dict]:
    prepared = []

    for record in records:
        prepared.append(
            {
                "id": record["id"],
                "text": record["text"],
                "label": label_map[record["label"]],
                "label_name": record["label"],
                "source": record.get("source", "unknown"),
            }
        )

    return prepared


def stratified_split(
    records: list[dict],
) -> tuple[list[dict], list[dict], list[dict]]:
    labels = [record["label"] for record in records]

    train_records, temp_records = train_test_split(
        records,
        test_size=0.20,
        random_state=RANDOM_SEED,
        stratify=labels,
    )

    temp_labels = [record["label"] for record in temp_records]

    validation_records, test_records = train_test_split(
        temp_records,
        test_size=0.50,
        random_state=RANDOM_SEED,
        stratify=temp_labels,
    )

    return train_records, validation_records, test_records


def print_distribution(
    name: str,
    records: list[dict],
) -> None:
    counts = Counter(record["label_name"] for record in records)

    print(f"\n{name}: {len(records)}")

    for label, count in sorted(counts.items()):
        percentage = count / len(records) * 100

        print(
            f"{label:25} "
            f"{count:3} "
            f"{percentage:6.2f}%"
        )


def tokenize_dataset(
    dataset: DatasetDict,
) -> DatasetDict:
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)

    def tokenize_batch(batch):
        return tokenizer(
            batch["text"],
            truncation=True,
            max_length=MAX_LENGTH,
        )

    return dataset.map(
        tokenize_batch,
        batched=True,
        desc="Tokenizing",
    )


def main() -> None:
    records = load_jsonl(INPUT_FILE)

    label_map = load_label_map(LABEL_MAP_FILE)

    prepared_records = prepare_records(
        records,
        label_map,
    )

    train_records, validation_records, test_records = stratified_split(
        prepared_records
    )

    print_distribution(
        "TRAIN",
        train_records,
    )

    print_distribution(
        "VALIDATION",
        validation_records,
    )

    print_distribution(
        "TEST",
        test_records,
    )

    dataset = DatasetDict(
        {
            "train": Dataset.from_list(train_records),
            "validation": Dataset.from_list(validation_records),
            "test": Dataset.from_list(test_records),
        }
    )

    tokenized_dataset = tokenize_dataset(dataset)

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    tokenized_dataset.save_to_disk(
        str(OUTPUT_DIR)
    )

    print(
        f"\nSaved tokenized dataset to:\n{OUTPUT_DIR}"
    )

    print("\nExample tokenized record:")
    print(tokenized_dataset["train"][0])


if __name__ == "__main__":
    main()