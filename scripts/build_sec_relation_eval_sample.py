from __future__ import annotations

import json
import random
from pathlib import Path

import spacy

from src.nlp.relation_extraction import RelationExtractor


PROCESSED_SEC_ROOT = Path("data/processed/sec")
TARGETS_PATH = Path("data/seed/sec_10k_targets.json")
OUTPUT_PATH = Path("data/evaluation/sec_relation_annotation_sample.jsonl")
SAMPLE_SIZE = 250
POSITIVE_FRACTION = 0.60
RANDOM_SEED = 38


def _target_names() -> set[str]:
    payload = json.loads(TARGETS_PATH.read_text(encoding="utf-8"))
    return {str(item["name"]).strip() for item in payload}


def _iter_filing_chunks() -> list[tuple[str, str, str]]:
    target_names = _target_names()
    rows: list[tuple[str, str, str]] = []

    for path in sorted(PROCESSED_SEC_ROOT.rglob("processed.json")):
        filing = json.loads(path.read_text(encoding="utf-8"))
        company_name = str(filing.get("company_name", "")).strip()
        if company_name not in target_names:
            continue

        accession = str(filing.get("accession_number", "")).strip()
        for section in filing.get("sections", []):
            for chunk in section.get("chunks", []):
                text = str(chunk.get("text", "")).strip()
                if text:
                    rows.append((company_name, accession, text))

    return rows


def _collect_sentences(nlp) -> list[dict]:
    extractor = RelationExtractor(nlp)
    seen: set[tuple[str, str, str]] = set()
    rows: list[dict] = []

    for company_name, accession, chunk_text in _iter_filing_chunks():
        doc = nlp(chunk_text)
        for sentence in doc.sents:
            text = sentence.text.strip()
            if len(text) < 40:
                continue

            key = (company_name, accession, text)
            if key in seen:
                continue
            seen.add(key)

            predicted = extractor.extract(text)
            rows.append(
                {
                    "company_name": company_name,
                    "accession_number": accession,
                    "source_sentence": text,
                    "extractor_candidate": bool(predicted),
                }
            )

    return rows


def _sample(rows: list[dict]) -> list[dict]:
    rng = random.Random(RANDOM_SEED)
    positives = [row for row in rows if row["extractor_candidate"]]
    negatives = [row for row in rows if not row["extractor_candidate"]]

    desired_positive = round(SAMPLE_SIZE * POSITIVE_FRACTION)
    positive_count = min(desired_positive, len(positives))
    negative_count = min(SAMPLE_SIZE - positive_count, len(negatives))

    # Backfill from whichever pool still has capacity.
    remaining = SAMPLE_SIZE - positive_count - negative_count
    if remaining > 0:
        extra_positive = min(remaining, len(positives) - positive_count)
        positive_count += extra_positive
        remaining -= extra_positive
    if remaining > 0:
        negative_count += min(remaining, len(negatives) - negative_count)

    selected = [
        *rng.sample(positives, positive_count),
        *rng.sample(negatives, negative_count),
    ]
    rng.shuffle(selected)

    output: list[dict] = []
    for index, row in enumerate(selected, start=1):
        output.append(
            {
                "sample_id": f"sec-rel-{index:04d}",
                "company_name": row["company_name"],
                "accession_number": row["accession_number"],
                "source_sentence": row["source_sentence"],
                "annotation_status": "UNREVIEWED",
                "gold_relations": None,
            }
        )

    return output


def main() -> None:
    nlp = spacy.load("en_core_web_sm")
    rows = _collect_sentences(nlp)
    sample = _sample(rows)

    if not sample:
        raise RuntimeError("No SEC evaluation sentences were discovered.")

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_PATH.open("w", encoding="utf-8") as file:
        for row in sample:
            file.write(json.dumps(row, ensure_ascii=False) + "\n")

    print("===== SEC RELATION EVALUATION SAMPLE =====")
    print(f"Available sentences: {len(rows)}")
    print(f"Sampled sentences: {len(sample)}")
    print(f"Random seed: {RANDOM_SEED}")
    print(f"Output: {OUTPUT_PATH}")
    print("==========================================")


if __name__ == "__main__":
    main()
