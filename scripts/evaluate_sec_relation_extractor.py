from __future__ import annotations

import json
from pathlib import Path

import spacy

from src.graph.ingestion.resolution import resolve_graph_candidates
from src.nlp.relation_extraction import RelationExtractor
from src.nlp.triplet_extractor import GraphCandidate


GOLD_PATH = Path("data/evaluation/sec_relation_balanced_annotation_sample.jsonl")
REPORT_PATH = Path("data/evaluation/sec_relation_balanced_evaluation_report.json")
MISMATCH_PATH = Path("data/evaluation/sec_relation_balanced_mismatches.jsonl")


def _relation_to_graph(candidate) -> GraphCandidate:
    return GraphCandidate(
        subject=candidate.subject,
        predicate=candidate.relationship,
        object=candidate.object,
        source_sentence=candidate.source_sentence,
        subject_type=candidate.subject_type,
        object_type=candidate.object_type,
    )


def _key(*, subject: str, subject_type: str, relationship: str, object_name: str, object_type: str) -> tuple[str, str, str, str, str]:
    return (subject, subject_type, relationship, object_name, object_type)


def _gold_keys(row: dict) -> set[tuple[str, str, str, str, str]]:
    relations = row.get("gold_relations")
    if not isinstance(relations, list):
        raise ValueError(f"Reviewed row {row.get('sample_id')} must contain gold_relations list.")
    keys = set()
    for relation in relations:
        if not isinstance(relation, dict):
            raise ValueError(f"Invalid gold relation in {row.get('sample_id')}: {relation!r}")
        keys.add(_key(
            subject=str(relation["subject"]),
            subject_type=str(relation.get("subject_type", "Company")),
            relationship=str(relation["relationship"]),
            object_name=str(relation["object"]),
            object_type=str(relation.get("object_type", "Company")),
        ))
    return keys


def _prediction_keys(extractor: RelationExtractor, *, sentence: str, filing_company: str) -> set[tuple[str, str, str, str, str]]:
    raw = [_relation_to_graph(candidate) for candidate in extractor.extract(sentence)]
    resolved = resolve_graph_candidates(raw, filing_company=filing_company)
    return {
        _key(subject=c.subject, subject_type=c.subject_type, relationship=c.relationship, object_name=c.object, object_type=c.object_type)
        for c in resolved
    }


def _serialize(keys):
    return [
        {"subject": k[0], "subject_type": k[1], "relationship": k[2], "object": k[3], "object_type": k[4]}
        for k in sorted(keys)
    ]


def _safe_divide(numerator: int, denominator: int) -> float:
    return numerator / denominator if denominator else 0.0


def main() -> None:
    if not GOLD_PATH.exists():
        raise FileNotFoundError(f"Gold annotation file not found: {GOLD_PATH}")
    rows = [json.loads(line) for line in GOLD_PATH.read_text(encoding="utf-8").splitlines() if line.strip()]
    reviewed = [row for row in rows if row.get("annotation_status") == "REVIEWED"]
    if not reviewed:
        raise ValueError("No REVIEWED annotations found. Manually label the sample before evaluation.")

    positive_gold_sentences = sum(1 for row in reviewed if isinstance(row.get("gold_relations"), list) and row["gold_relations"])
    gold_relation_instances = sum(len(row["gold_relations"]) for row in reviewed if isinstance(row.get("gold_relations"), list))

    nlp = spacy.load("en_core_web_sm")
    extractor = RelationExtractor(nlp)
    true_positive = false_positive = false_negative = exact_sentence_matches = 0
    prediction_union = set()
    gold_union = set()
    mismatches = []

    for row in reviewed:
        gold = _gold_keys(row)
        predicted = _prediction_keys(extractor, sentence=str(row["source_sentence"]), filing_company=str(row["company_name"]))
        fp = predicted - gold
        fn = gold - predicted
        true_positive += len(gold & predicted)
        false_positive += len(fp)
        false_negative += len(fn)
        exact_sentence_matches += int(gold == predicted)
        prediction_union.update(predicted)
        gold_union.update(gold)
        if fp or fn:
            mismatches.append({
                "sample_id": row.get("sample_id"),
                "company_name": row.get("company_name"),
                "source_sentence": row.get("source_sentence"),
                "false_positives": _serialize(fp),
                "false_negatives": _serialize(fn),
            })

    precision = _safe_divide(true_positive, true_positive + false_positive)
    recall = _safe_divide(true_positive, true_positive + false_negative)
    f1 = _safe_divide(2 * precision * recall, precision + recall)
    exact_sentence_accuracy = _safe_divide(exact_sentence_matches, len(reviewed))

    report = {
        "benchmark": {"path": str(GOLD_PATH), "reviewed_sentences": len(reviewed), "positive_gold_sentences": positive_gold_sentences, "gold_relation_instances": gold_relation_instances},
        "true_positive": true_positive, "false_positive": false_positive, "false_negative": false_negative,
        "precision": precision, "recall": recall, "f1": f1, "exact_sentence_accuracy": exact_sentence_accuracy,
        "unique_gold_relations": len(gold_union), "unique_predicted_relations": len(prediction_union),
        "mismatch_path": str(MISMATCH_PATH),
        "historical_baseline": {"companies_with_sec_edges": 12, "production_10k_companies": 27, "unique_relationships": 35, "note": "Pre-repair graph coverage baseline; not directly comparable to sentence-level Precision/Recall/F1."},
    }
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, indent=2), encoding="utf-8")
    MISMATCH_PATH.write_text("\n".join(json.dumps(row, ensure_ascii=False) for row in mismatches) + ("\n" if mismatches else ""), encoding="utf-8")

    print("===== BALANCED SEC RELATION EXTRACTOR EVALUATION =====")
    print(f"Reviewed sentences: {len(reviewed)}")
    print(f"Positive gold sentences: {positive_gold_sentences}")
    print(f"Gold relation instances: {gold_relation_instances}")
    print(f"TP: {true_positive}")
    print(f"FP: {false_positive}")
    print(f"FN: {false_negative}")
    print(f"Precision: {precision:.4f}")
    print(f"Recall: {recall:.4f}")
    print(f"F1: {f1:.4f}")
    print(f"Exact sentence accuracy: {exact_sentence_accuracy:.4f}")
    print(f"Unique gold relations: {len(gold_union)}")
    print(f"Unique predicted relations: {len(prediction_union)}")
    print(f"Mismatch rows: {len(mismatches)}")
    print(f"Mismatch details: {MISMATCH_PATH}")
    print("Historical graph baseline: 12/27 companies, 35 unique relationships")
    print("NOTE: historical graph coverage is context, not a sentence-level metric.")
    print(f"Report: {REPORT_PATH}")
    print("======================================================")


if __name__ == "__main__":
    main()
