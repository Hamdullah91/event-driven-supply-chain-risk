from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path

from src.graph.ingestion.resolution import (
    _resolve_object,
    _resolve_subject,
    resolve_graph_candidates,
)
from src.nlp.triplet_extractor import GraphCandidate
from src.nlp.validation.relationship_rules import VALID_RELATIONSHIPS


AUDIT_PATH = Path("audit_sec_final2.txt")
TARGETS_PATH = Path("data/seed/sec_10k_targets.json")

COMPANY_RE = re.compile(r"^Company:\s*(.+?)\s*$")
RESOLVED_RE = re.compile(r"^Resolved graph candidates:\s*(\d+)\s*$")
RAW_TRIPLE_RE = re.compile(r"^\[(\d+)\]\s+(.+?)\s+-\[([A-Z_]+)\]->\s+(.+?)\s*$")
TYPES_RE = re.compile(r"^\s*types:\s*(.+?)\s*->\s*(.+?)\s*$")
SENTENCE_RE = re.compile(r"^\s*sentence:\s*(.*)$")


def _load_target_names() -> set[str]:
    targets = json.loads(TARGETS_PATH.read_text(encoding="utf-8"))
    return {str(target["name"]).strip() for target in targets}


def _normalize_type(value: str) -> str | None:
    cleaned = value.strip()
    if not cleaned or cleaned.lower() == "unknown":
        return None
    return cleaned


def _parse_audit(path: Path) -> list[dict]:
    if not path.exists():
        raise FileNotFoundError(
            f"Audit file not found: {path}. Run the SEC audit first."
        )

    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    filings: list[dict] = []
    current: dict | None = None
    in_raw = False
    pending: GraphCandidate | None = None

    def flush_pending() -> None:
        nonlocal pending
        if current is not None and pending is not None:
            current["raw_candidates"].append(pending)
        pending = None

    for line in lines:
        company_match = COMPANY_RE.match(line)
        if company_match:
            flush_pending()
            if current is not None:
                filings.append(current)
            current = {
                "company": company_match.group(1).strip(),
                "resolved_count": None,
                "raw_candidates": [],
            }
            in_raw = False
            continue

        if current is None:
            continue

        resolved_match = RESOLVED_RE.match(line)
        if resolved_match:
            current["resolved_count"] = int(resolved_match.group(1))
            continue

        if line.strip() == "RAW TRIPLETS":
            flush_pending()
            in_raw = True
            continue

        if line.strip() == "RESOLVED CANDIDATES":
            flush_pending()
            in_raw = False
            continue

        if not in_raw:
            continue

        triple_match = RAW_TRIPLE_RE.match(line)
        if triple_match:
            flush_pending()
            pending = GraphCandidate(
                subject=triple_match.group(2).strip(),
                predicate=triple_match.group(3).strip(),
                object=triple_match.group(4).strip(),
                source_sentence="",
            )
            continue

        types_match = TYPES_RE.match(line)
        if types_match and pending is not None:
            pending = GraphCandidate(
                subject=pending.subject,
                predicate=pending.predicate,
                object=pending.object,
                source_sentence=pending.source_sentence,
                confidence=pending.confidence,
                subject_type=_normalize_type(types_match.group(1)),
                object_type=_normalize_type(types_match.group(2)),
            )
            continue

        sentence_match = SENTENCE_RE.match(line)
        if sentence_match and pending is not None:
            pending = GraphCandidate(
                subject=pending.subject,
                predicate=pending.predicate,
                object=pending.object,
                source_sentence=sentence_match.group(1).strip(),
                confidence=pending.confidence,
                subject_type=pending.subject_type,
                object_type=pending.object_type,
            )

    flush_pending()
    if current is not None:
        filings.append(current)

    return filings


def main() -> None:
    target_names = _load_target_names()
    filings = _parse_audit(AUDIT_PATH)
    zero_coverage: list[str] = []

    for filing in filings:
        company = filing["company"]
        if company not in target_names:
            continue

        if filing["resolved_count"] not in {0, None}:
            continue

        raw_candidates: list[GraphCandidate] = filing["raw_candidates"]
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

            subject = _resolve_subject(candidate, filing_company=company)
            if subject is None:
                subject_rejections += 1
                continue

            object_value = _resolve_object(candidate, filing_company=company)
            if object_value is None:
                object_rejections += 1
                unresolved_objects[candidate.object.strip()] += 1
                continue

            _, subject_type = subject
            _, object_type = object_value
            relationship = candidate.predicate
            if relationship == "USES" and object_type == "Company":
                relationship = "DEPENDS_ON"

            if (subject_type, relationship, object_type) not in VALID_RELATIONSHIPS:
                ontology_rejections += 1

        zero_coverage.append(company)

        print(
            "ZERO_COVERAGE | "
            f"company={company} | "
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
                    for name, count in unresolved_objects.most_common(10)
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
