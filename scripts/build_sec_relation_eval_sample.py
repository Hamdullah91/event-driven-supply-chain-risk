from __future__ import annotations

import json
import random
import re
from pathlib import Path

import spacy

from scripts.ingest_sec_graph import load_target_company_names
from src.graph.ingestion.resolution import resolve_graph_candidates
from src.nlp.relation_extraction import RelationExtractor
from src.nlp.triplet_extractor import GraphCandidate


PROCESSED_SEC_ROOT = Path("data/processed/sec")
OUTPUT_PATH = Path("data/evaluation/sec_relation_balanced_annotation_sample.jsonl")
SAMPLE_SIZE = 100
POSITIVE_SIZE = 50
NEGATIVE_SIZE = 50
RANDOM_SEED = 38
NLP_BATCH_SIZE = 16

# Broad lexical screen used only to find hard negatives. Gold labels remain
# manual: production predictions are included only as annotation hints.
RELATION_TRIGGER_PATTERN = re.compile(
    r"\b("
    r"depend(?:s|ed|ing)?|rely|relies|relied|relying|"
    r"source(?:s|d|ing)?|purchase(?:s|d|ing)?|procure(?:s|d|ing)?|"
    r"obtain(?:s|ed|ing)?|outsource(?:s|d|ing)?|"
    r"supply|supplies|supplied|supplying|provide(?:s|d|ing)?|"
    r"deliver(?:s|ed|ing)?|produce(?:s|d|ing)?|"
    r"manufacture(?:s|d|ing)?|fabricate(?:s|d|ing)?|"
    r"assemble(?:s|d|ing)?|build(?:s|ing|t)?|"
    r"use(?:s|d|ing)?|utilize(?:s|d|ing)?|operate(?:s|d|ing)?|"
    r"own(?:s|ed|ing)?"
    r")\b",
    re.IGNORECASE,
)


def _relation_to_graph(candidate) -> GraphCandidate:
    return GraphCandidate(
        subject=candidate.subject,
        predicate=candidate.relationship,
        object=candidate.object,
        source_sentence=candidate.source_sentence,
        subject_type=candidate.subject_type,
        object_type=candidate.object_type,
    )


def _iter_filing_chunks() -> list[tuple[str, str, str]]:
    target_names = load_target_company_names()
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


def _prediction_hint(extractor: RelationExtractor, sentence: str, company: str) -> list[dict]:
    raw = [_relation_to_graph(candidate) for candidate in extractor.extract(sentence)]
    resolved = resolve_graph_candidates(raw, filing_company=company)
    return [
        {
            "subject": candidate.subject,
            "subject_type": candidate.subject_type,
            "relationship": candidate.relationship,
            "object": candidate.object,
            "object_type": candidate.object_type,
        }
        for candidate in resolved
    ]


def _collect_sentences(nlp, extractor: RelationExtractor) -> list[dict]:
    chunks = _iter_filing_chunks()
    seen: set[tuple[str, str, str]] = set()
    rows: list[dict] = []
    texts = [chunk_text for _, _, chunk_text in chunks]

    print(f"SEC chunks discovered: {len(chunks)}", flush=True)
    print("Segmenting production 10-K/20-F sentences...", flush=True)

    for index, (metadata, doc) in enumerate(
        zip(chunks, nlp.pipe(texts, batch_size=NLP_BATCH_SIZE), strict=True),
        start=1,
    ):
        company_name, accession, _ = metadata
        for sentence in doc.sents:
            text = sentence.text.strip()
            if len(text) < 40:
                continue
            key = (company_name, accession, text)
            if key in seen:
                continue
            seen.add(key)
            rows.append(
                {
                    "company_name": company_name,
                    "accession_number": accession,
                    "source_sentence": text,
                    "lexical_relation_trigger": bool(RELATION_TRIGGER_PATTERN.search(text)),
                }
            )

        if index % 100 == 0 or index == len(chunks):
            print(f"Processed chunks: {index}/{len(chunks)} | unique sentences: {len(rows)}", flush=True)

    print("Running production extractor to identify resolvable positive candidates...", flush=True)
    for index, row in enumerate(rows, start=1):
        row["prediction_hint"] = _prediction_hint(
            extractor,
            row["source_sentence"],
            row["company_name"],
        )
        if index % 1000 == 0 or index == len(rows):
            print(f"Scored sentences: {index}/{len(rows)}", flush=True)

    return rows


def _sample(rows: list[dict]) -> list[dict]:
    rng = random.Random(RANDOM_SEED)
    predicted_positive = [row for row in rows if row["prediction_hint"]]
    hard_negative = [
        row
        for row in rows
        if not row["prediction_hint"] and row["lexical_relation_trigger"]
    ]
    easy_negative = [
        row
        for row in rows
        if not row["prediction_hint"] and not row["lexical_relation_trigger"]
    ]

    if len(predicted_positive) < POSITIVE_SIZE:
        raise RuntimeError(
            "Not enough production-positive SEC sentences for a 50-positive benchmark. "
            f"Found {len(predicted_positive)}. Do not synthesize positives; manually review "
            "all available production positives and supplement with independently selected "
            "real SEC sentences if needed."
        )

    positives = rng.sample(predicted_positive, POSITIVE_SIZE)
    hard_count = min(NEGATIVE_SIZE, len(hard_negative))
    negatives = rng.sample(hard_negative, hard_count)
    if len(negatives) < NEGATIVE_SIZE:
        negatives.extend(rng.sample(easy_negative, NEGATIVE_SIZE - len(negatives)))

    selected = [("POSITIVE_CANDIDATE", row) for row in positives]
    selected.extend(("HARD_NEGATIVE_CANDIDATE", row) for row in negatives)
    rng.shuffle(selected)

    output: list[dict] = []
    for index, (stratum, row) in enumerate(selected, start=1):
        output.append(
            {
                "sample_id": f"sec-balanced-{index:04d}",
                "stratum": stratum,
                "company_name": row["company_name"],
                "accession_number": row["accession_number"],
                "source_sentence": row["source_sentence"],
                "prediction_hint": row["prediction_hint"],
                "annotation_status": "UNREVIEWED",
                "gold_relations": None,
            }
        )
    return output


def main() -> None:
    print("Loading spaCy model...", flush=True)
    nlp = spacy.load("en_core_web_sm")
    extractor = RelationExtractor(nlp)
    rows = _collect_sentences(nlp, extractor)

    predicted_positive_count = sum(1 for row in rows if row["prediction_hint"])
    hard_negative_count = sum(
        1 for row in rows
        if not row["prediction_hint"] and row["lexical_relation_trigger"]
    )

    print("===== BALANCED SEC EVALUATION POOLS =====")
    print(f"Available sentences: {len(rows)}")
    print(f"Production-positive candidates: {predicted_positive_count}")
    print(f"Hard-negative candidates: {hard_negative_count}")

    sample = _sample(rows)
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_PATH.open("w", encoding="utf-8") as file:
        for row in sample:
            file.write(json.dumps(row, ensure_ascii=False) + "\n")

    print(f"Sampled sentences: {len(sample)}")
    print(f"Positive candidates: {POSITIVE_SIZE}")
    print(f"Negative candidates: {NEGATIVE_SIZE}")
    print(f"Random seed: {RANDOM_SEED}")
    print(f"Output: {OUTPUT_PATH}")
    print("IMPORTANT: prediction_hint is not gold. Manually review every row before evaluation.")
    print("=========================================")


if __name__ == "__main__":
    main()
