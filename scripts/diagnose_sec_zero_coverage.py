from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

import spacy

from src.graph.ingestion.resolution import (
    _resolve_object,
    _resolve_subject,
    resolve_graph_candidates,
)
from src.nlp.triplet_extractor import TripletExtractor


PROCESSED_SEC_ROOT = Path("data/processed/sec")
TARGETS_PATH = Path("data/seed/sec_10k_targets.json")


def _load_target_names() -> set[str]:
    targets = json.loads(TARGETS_PATH.read_text(encoding="utf-8"))
    return {str(target["name"]).strip() for target in targets}


def main() -> None:
    target_names = _load_target_names()
    nlp = spacy.load("en_core_web_sm")
    extractor = TripletExtractor(nlp)

    zero_coverage = []

    for processed_file in sorted(PROCESSED_SEC_ROOT.rglob("processed.json")):
        filing = json.loads(processed_file.read_text(encoding="utf-8"))
        company = str(filing.get("company_name", "")).strip()

        if company not in target_names:
            continue

        sections = filing.get("sections", [])
        chunks = [
            chunk
            for section in sections
            for chunk in section.get("chunks", [])
            if chunk.get("text", "").strip()
        ]
        text_chars = sum(len(chunk["text"]) for chunk in chunks)

        raw_candidates = []
        for chunk in chunks:
            raw_candidates.extend(extractor.extract(chunk["text"]))

        resolved = resolve_graph_candidates(
            raw_candidates,
            filing_company=company,
        )

        if resolved:
            continue

        subject_rejections = 0
        object_rejections = 0
        ontology_rejections = 0
        object_type_counts: Counter[str] = Counter()
        predicate_counts: Counter[str] = Counter()
        unresolved_objects: Counter[str] = Counter()

        for candidate in raw_candidates:
            predicate_counts[candidate.predicate] += 1
            object_type_counts[candidate.object_type or "unknown"] += 1

            subject = _resolve_subject(
                candidate,
                filing_company=company,
            )
            if subject is None:
                subject_rejections += 1
                continue

            object_value = _resolve_object(
                candidate,
                filing_company=company,
            )
            if object_value is None:
                object_rejections += 1
                unresolved_objects[candidate.object.strip()] += 1
                continue

            subject_name, subject_type = subject
            object_name, object_type = object_value
            relationship = candidate.predicate
            if relationship == "USES" and object_type == "Company":
                relationship = "DEPENDS_ON"

            from src.nlp.validation.relationship_rules import VALID_RELATIONSHIPS

            if (subject_type, relationship, object_type) not in VALID_RELATIONSHIPS:
                ontology_rejections += 1

        zero_coverage.append(company)

        print(
            "ZERO_COVERAGE | "
            f"company={company} | "
            f"sections={len(sections)} | "
            f"chunks={len(chunks)} | "
            f"chars={text_chars} | "
            f"raw={len(raw_candidates)} | "
            f"subject_reject={subject_rejections} | "
            f"object_reject={object_rejections} | "
            f"ontology_reject={ontology_rejections}"
        )
        print(
            "  predicates="
            + ", ".join(
                f"{name}:{count}"
                for name, count in sorted(predicate_counts.items())
            )
        )
        print(
            "  object_types="
            + ", ".join(
                f"{name}:{count}"
                for name, count in sorted(object_type_counts.items())
            )
        )
        if unresolved_objects:
            print(
                "  top_unresolved_objects="
                + " | ".join(
                    f"{name} ({count})"
                    for name, count in unresolved_objects.most_common(8)
                )
            )

        for index, candidate in enumerate(raw_candidates[:5], start=1):
            print(
                f"  sample[{index}] {candidate.subject} "
                f"-[{candidate.predicate}]-> {candidate.object} "
                f"({candidate.subject_type or 'unknown'} -> "
                f"{candidate.object_type or 'unknown'})"
            )

    print()
    print(
        "ZERO_COVERAGE_TOTAL | "
        f"count={len(zero_coverage)} | "
        f"companies={'; '.join(zero_coverage)}"
    )


if __name__ == "__main__":
    main()
