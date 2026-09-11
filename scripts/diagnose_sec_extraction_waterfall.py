from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path

from scripts.diagnose_sec_zero_coverage import _normalize_company_name, _parse_audit


PROCESSED_ROOT = Path("data/processed/sec")
TARGETS_PATH = Path("data/seed/sec_10k_targets.json")
AUDIT_PATH = Path("audit_sec_final2.txt")
OUTPUT_PATH = Path("outputs/diagnostics/sec_extraction_waterfall.json")

# Broad diagnostic vocabulary only. These phrases do not create graph edges.
# They answer whether potentially useful supply-chain language exists in text.
RELATION_TRIGGER_PATTERNS: dict[str, tuple[str, ...]] = {
    "DEPENDENCY": (
        r"\bdepend(?:s|ed|ing)?\s+on\b",
        r"\bdependent\s+(?:on|upon)\b",
        r"\brely|relies|relied|relying\b",
        r"\bsource(?:s|d|ing)?\s+from\b",
        r"\bsourced\s+from\b",
        r"\bpurchase(?:s|d|ing)?\s+from\b",
        r"\bprocure(?:s|d|ment|ing)?\s+from\b",
        r"\bobtain(?:s|ed|ing)?\b.{0,80}\bfrom\b",
        r"\boutsource(?:s|d|ing)?\b",
        r"\bfabricated\s+by\b",
        r"\bmanufactured\s+by\b",
        r"\bcontract manufacturer(?:s)?\b",
        r"\bfoundr(?:y|ies)\b",
        r"\bsole[- ]source(?:d)?\b",
        r"\bsingle[- ]source(?:d)?\b",
        r"\bthird[- ]party manufacturer(?:s)?\b",
    ),
    "SUPPLY": (
        r"\bsuppl(?:y|ies|ied|ier|iers)\b",
        r"\bprovide(?:s|d|ing)?\b",
        r"\bdeliver(?:s|ed|ing|y|ies)\b",
        r"\bvendor(?:s)?\b",
    ),
    "PRODUCTION": (
        r"\bproduce(?:s|d|ing)?\b",
        r"\bmanufacture(?:s|d|ing|r|rs)?\b",
        r"\bfabricate(?:s|d|ing)?\b",
        r"\bassembl(?:e|es|ed|ing|y)\b",
        r"\bbuild(?:s|ing|t)?\b",
    ),
    "FACILITY": (
        r"\boperate(?:s|d|ing)?\b",
        r"\bown(?:s|ed|ing)?\b",
        r"\bfacilit(?:y|ies)\b",
        r"\bplant(?:s)?\b",
        r"\bfab(?:s)?\b",
        r"\bfactor(?:y|ies)\b",
    ),
    "USE": (
        r"\buse(?:s|d|ing)?\b",
        r"\butiliz(?:e|es|ed|ing)\b",
    ),
}

SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9])")


def _load_targets() -> dict[str, dict]:
    targets = json.loads(TARGETS_PATH.read_text(encoding="utf-8"))
    return {
        _normalize_company_name(str(target["name"])): target
        for target in targets
    }


def _load_audit_index() -> dict[str, dict]:
    filings = _parse_audit(AUDIT_PATH)
    return {
        _normalize_company_name(str(filing["company"])): filing
        for filing in filings
    }


def _find_processed_filings() -> dict[str, Path]:
    result: dict[str, Path] = {}
    for path in PROCESSED_ROOT.rglob("processed.json"):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        company = str(data.get("company_name") or "").strip()
        if company:
            result[_normalize_company_name(company)] = path
    return result


def _entity_counts(entities_path: Path) -> tuple[int, Counter[str], Counter[str]]:
    if not entities_path.exists():
        return 0, Counter(), Counter()

    data = json.loads(entities_path.read_text(encoding="utf-8"))
    total = 0
    nlp_labels: Counter[str] = Counter()
    domain_types: Counter[str] = Counter()

    for section in data.get("sections", []):
        for entity in section.get("entities", []):
            total += 1
            nlp_labels[str(entity.get("nlp_label") or "unknown")] += 1
            domain_types[str(entity.get("domain_type") or "unknown")] += 1

    return total, nlp_labels, domain_types


def _trigger_counts(text: str) -> tuple[int, Counter[str], list[str]]:
    counts: Counter[str] = Counter()
    matched_sentences: list[str] = []

    for sentence in SENTENCE_SPLIT_RE.split(text):
        sentence = " ".join(sentence.split())
        if not sentence:
            continue

        matched = False
        for family, patterns in RELATION_TRIGGER_PATTERNS.items():
            if any(re.search(pattern, sentence, flags=re.IGNORECASE) for pattern in patterns):
                counts[family] += 1
                matched = True

        if matched and len(matched_sentences) < 8:
            matched_sentences.append(sentence[:500])

    return sum(counts.values()), counts, matched_sentences


def _classify_failure(
    *,
    text_chars: int,
    trigger_hits: int,
    raw_triplets: int,
    resolved_edges: int,
) -> str:
    if text_chars == 0:
        return "NO_SECTION_TEXT"
    if trigger_hits == 0:
        return "NO_RELATION_TRIGGER_LANGUAGE"
    if raw_triplets == 0:
        return "TRIGGERS_PRESENT_BUT_NO_RAW_TRIPLETS"
    if resolved_edges == 0:
        return "RAW_TRIPLETS_REJECTED_DOWNSTREAM"
    return "HAS_RESOLVED_RELATIONSHIPS"


def main() -> None:
    targets = _load_targets()
    audit_index = _load_audit_index()
    processed_index = _find_processed_filings()
    reports: list[dict] = []

    for normalized_name, target in sorted(
        targets.items(),
        key=lambda item: item[1]["name"].lower(),
    ):
        company = str(target["name"])
        processed_path = processed_index.get(normalized_name)

        if processed_path is None:
            report = {
                "company": company,
                "company_id": target.get("company_id"),
                "status": "PROCESSED_FILE_MISSING",
            }
            reports.append(report)
            print(
                "WATERFALL | "
                f"company={company} | status=PROCESSED_FILE_MISSING"
            )
            continue

        data = json.loads(processed_path.read_text(encoding="utf-8"))
        sections = data.get("sections", [])
        section_count = len(sections)
        chunk_count = sum(len(section.get("chunks", [])) for section in sections)
        section_chars = {
            str(section.get("item_number") or "unknown"): len(
                str(section.get("text") or "")
            )
            for section in sections
        }
        full_text = "\n".join(str(section.get("text") or "") for section in sections)
        text_chars = len(full_text)
        sentence_count = sum(
            1
            for sentence in SENTENCE_SPLIT_RE.split(full_text)
            if sentence.strip()
        )

        trigger_hits, trigger_families, trigger_samples = _trigger_counts(full_text)
        entity_total, nlp_labels, domain_types = _entity_counts(
            processed_path.parent / "entities.json"
        )

        audit = audit_index.get(normalized_name, {})
        raw_triplets = len(audit.get("raw_candidates", []))
        resolved_edges = int(audit.get("resolved_count") or 0)

        status = _classify_failure(
            text_chars=text_chars,
            trigger_hits=trigger_hits,
            raw_triplets=raw_triplets,
            resolved_edges=resolved_edges,
        )

        report = {
            "company": company,
            "company_id": target.get("company_id"),
            "cik": target.get("cik"),
            "processed_file": str(processed_path),
            "section_count": section_count,
            "section_chars": section_chars,
            "chunk_count": chunk_count,
            "text_chars": text_chars,
            "sentence_count": sentence_count,
            "entity_mentions": entity_total,
            "entity_nlp_labels": dict(nlp_labels),
            "entity_domain_types": dict(domain_types),
            "relation_trigger_hits": trigger_hits,
            "relation_trigger_families": dict(trigger_families),
            "relation_trigger_samples": trigger_samples,
            "raw_triplets": raw_triplets,
            "resolved_edges": resolved_edges,
            "status": status,
        }
        reports.append(report)

        trigger_summary = ",".join(
            f"{name}:{count}"
            for name, count in sorted(trigger_families.items())
        ) or "none"
        section_summary = ",".join(
            f"{name}:{count}"
            for name, count in sorted(section_chars.items())
        ) or "none"

        print(
            "WATERFALL | "
            f"company={company} | "
            f"sections={section_count} | "
            f"section_chars={section_summary} | "
            f"chunks={chunk_count} | "
            f"chars={text_chars} | "
            f"sentences={sentence_count} | "
            f"entities={entity_total} | "
            f"triggers={trigger_hits}({trigger_summary}) | "
            f"raw={raw_triplets} | "
            f"resolved={resolved_edges} | "
            f"status={status}"
        )

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(
        json.dumps(reports, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    status_counts = Counter(report["status"] for report in reports)
    print()
    print(
        "WATERFALL_SUMMARY | "
        + " | ".join(
            f"{status}={count}"
            for status, count in sorted(status_counts.items())
        )
    )
    print(f"WATERFALL_OUTPUT | path={OUTPUT_PATH}")


if __name__ == "__main__":
    main()
