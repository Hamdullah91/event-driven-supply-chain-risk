from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

import spacy

from src.graph.ingestion.resolution import resolve_graph_candidates
from src.nlp.relation_extraction import RelationExtractor
from src.nlp.triplet_extractor import GraphCandidate, TripletExtractor


PROCESSED_SEC_ROOT = Path("data/processed/sec")
TARGETS_PATH = Path("data/seed/sec_10k_targets.json")


def _load_target_names() -> set[str]:
    payload = json.loads(TARGETS_PATH.read_text(encoding="utf-8"))
    return {item["name"] for item in payload}


def _relation_to_graph(candidate) -> GraphCandidate:
    return GraphCandidate(
        subject=candidate.subject,
        predicate=candidate.relationship,
        object=candidate.object,
        source_sentence=candidate.source_sentence,
        subject_type=candidate.subject_type,
        object_type=candidate.object_type,
    )


def _extract_texts(filing: dict) -> list[str]:
    texts: list[str] = []
    for section in filing.get("sections", []):
        for chunk in section.get("chunks", []):
            text = chunk.get("text", "").strip()
            if text:
                texts.append(text)
    return texts


def _key(candidate) -> tuple[str, str, str, str, str]:
    return (
        candidate.subject,
        candidate.subject_type,
        candidate.relationship,
        candidate.object,
        candidate.object_type,
    )


def main() -> None:
    target_names = _load_target_names()
    processed_files = sorted(PROCESSED_SEC_ROOT.rglob("processed.json"))

    nlp = spacy.load("en_core_web_sm")
    legacy_extractor = TripletExtractor(nlp)
    new_extractor = RelationExtractor(nlp)

    global_counts = Counter()
    audited = 0

    for processed_file in processed_files:
        filing = json.loads(processed_file.read_text(encoding="utf-8"))
        company_name = filing.get("company_name", "")
        if company_name not in target_names:
            continue

        audited += 1
        texts = _extract_texts(filing)

        legacy_raw = []
        new_raw = []

        for text in texts:
            legacy_raw.extend(legacy_extractor.extract(text))
            new_raw.extend(
                _relation_to_graph(candidate)
                for candidate in new_extractor.extract(text)
            )

        legacy_resolved = resolve_graph_candidates(
            legacy_raw,
            filing_company=company_name,
        )
        new_resolved = resolve_graph_candidates(
            new_raw,
            filing_company=company_name,
        )

        legacy_keys = {_key(candidate) for candidate in legacy_resolved}
        new_keys = {_key(candidate) for candidate in new_resolved}
        overlap = legacy_keys & new_keys
        new_only = new_keys - legacy_keys
        legacy_only = legacy_keys - new_keys

        global_counts["legacy_raw"] += len(legacy_raw)
        global_counts["new_raw"] += len(new_raw)
        global_counts["legacy_resolved"] += len(legacy_keys)
        global_counts["new_resolved"] += len(new_keys)
        global_counts["overlap"] += len(overlap)
        global_counts["new_only"] += len(new_only)
        global_counts["legacy_only"] += len(legacy_only)

        print(
            "COMPARE_SUMMARY | "
            f"company={company_name} | "
            f"legacy_raw={len(legacy_raw)} | "
            f"new_raw={len(new_raw)} | "
            f"legacy_resolved={len(legacy_keys)} | "
            f"new_resolved={len(new_keys)} | "
            f"overlap={len(overlap)} | "
            f"new_only={len(new_only)} | "
            f"legacy_only={len(legacy_only)}"
        )

        for label, values in (
            ("NEW_ONLY", sorted(new_only)),
            ("LEGACY_ONLY", sorted(legacy_only)),
        ):
            for subject, subject_type, relationship, object_name, object_type in values:
                print(
                    f"{label} | company={company_name} | "
                    f"({subject_type}) {subject} -[{relationship}]-> "
                    f"({object_type}) {object_name}"
                )

    print()
    print("=" * 80)
    print("SEC RELATION EXTRACTOR COMPARISON")
    print(f"Production filings audited: {audited}")
    for key in (
        "legacy_raw",
        "new_raw",
        "legacy_resolved",
        "new_resolved",
        "overlap",
        "new_only",
        "legacy_only",
    ):
        print(f"{key}: {global_counts[key]}")

    print(
        "COMPARE_GLOBAL | "
        f"filings={audited} | "
        f"legacy_raw={global_counts['legacy_raw']} | "
        f"new_raw={global_counts['new_raw']} | "
        f"legacy_resolved={global_counts['legacy_resolved']} | "
        f"new_resolved={global_counts['new_resolved']} | "
        f"overlap={global_counts['overlap']} | "
        f"new_only={global_counts['new_only']} | "
        f"legacy_only={global_counts['legacy_only']}"
    )


if __name__ == "__main__":
    main()
