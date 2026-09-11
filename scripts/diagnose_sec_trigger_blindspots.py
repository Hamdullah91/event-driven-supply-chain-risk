from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path

WATERFALL_PATH = Path("outputs/diagnostics/sec_extraction_waterfall.json")
PROCESSED_ROOT = Path("data/processed/sec")

BROAD_PATTERNS: dict[str, tuple[str, ...]] = {
    "DEPENDENCY": (
        r"\bdepend(?:s|ed|ing)?\s+on\b",
        r"\breli(?:es|ed|ance|ant)?\s+(?:on|upon)\b",
        r"\bsource(?:s|d|ing)?\s+from\b",
        r"\bpurchase(?:s|d|ing)?\s+from\b",
        r"\bprocure(?:s|d|ment|ing)?\s+from\b",
        r"\bobtain(?:s|ed|ing)?\b.{0,80}\bfrom\b",
        r"\boutsource(?:s|d|ing)?\b.{0,80}\bto\b",
        r"\bfabricat(?:e|es|ed|ion|ing)\b.{0,80}\bby\b",
        r"\bmanufactur(?:e|es|ed|ing)\b.{0,80}\bby\b",
        r"\bcontract manufacturer(?:s)?\b",
        r"\bthird[- ]party manufactur(?:er|ers|ing)\b",
        r"\bfoundr(?:y|ies)\b",
        r"\bsole[- ]source\b",
        r"\bsingle[- ]source\b",
    ),
    "SUPPLY": (
        r"\bsuppli(?:er|ers|es|ed|ying)\b",
        r"\bprovid(?:e|es|ed|ing)\b",
        r"\bdeliver(?:s|ed|ing|y)\b",
        r"\bvendor(?:s)?\b",
    ),
    "PRODUCTION": (
        r"\bproduc(?:e|es|ed|ing|tion)\b",
        r"\bmanufactur(?:e|es|ed|ing)\b",
        r"\bfabricat(?:e|es|ed|ing|ion)\b",
        r"\bassembl(?:e|es|ed|ing|y)\b",
        r"\bbuild(?:s|ing|built)?\b",
    ),
    "FACILITY": (
        r"\boperat(?:e|es|ed|ing)\b",
        r"\bown(?:s|ed|ing)?\b",
        r"\bfacilit(?:y|ies)\b",
        r"\bplant(?:s)?\b",
        r"\bfab(?:s)?\b",
        r"\bfactor(?:y|ies)\b",
    ),
    "MATERIAL_TECH": (
        r"\buse(?:s|d|ing)?\b",
        r"\butiliz(?:e|es|ed|ing)\b",
        r"\bwafer(?:s)?\b",
        r"\bsilicon\b",
        r"\blithium\b",
        r"\bcobalt\b",
        r"\bnickel\b",
        r"\bAI/ML\b",
        r"\bartificial intelligence\b",
        r"\bmachine learning\b",
    ),
}


def _load_waterfall() -> list[dict]:
    data = json.loads(WATERFALL_PATH.read_text(encoding="utf-8"))
    if isinstance(data, dict):
        for key in ("filings", "results", "records"):
            if isinstance(data.get(key), list):
                return data[key]
    if isinstance(data, list):
        return data
    raise ValueError("Unsupported waterfall JSON structure")


def _normalize(value: str) -> str:
    return " ".join(value.lower().split())


def _find_processed(company_name: str) -> Path | None:
    target = _normalize(company_name)
    for path in PROCESSED_ROOT.rglob("processed.json"):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if _normalize(str(data.get("company_name", ""))) == target:
            return path
    return None


def _sentences(text: str) -> list[str]:
    return [
        " ".join(part.split())
        for part in re.split(r"(?<=[.!?])\s+|\n+", text)
        if part.strip()
    ]


def main() -> None:
    records = _load_waterfall()
    targets = [
        record
        for record in records
        if record.get("status") == "NO_RELATION_TRIGGER_LANGUAGE"
    ]

    print(f"BLINDSPOT_TARGETS | count={len(targets)}")

    for record in targets:
        company = str(record.get("company_name") or record.get("company") or "").strip()
        processed_path = _find_processed(company)
        if processed_path is None:
            print(f"BLINDSPOT | company={company} | error=processed_file_not_found")
            continue

        data = json.loads(processed_path.read_text(encoding="utf-8"))
        text = "\n".join(
            str(section.get("text", ""))
            for section in data.get("sections", [])
            if section.get("text")
        )
        sentences = _sentences(text)

        category_counts: Counter[str] = Counter()
        phrase_counts: Counter[str] = Counter()
        matched_sentences: list[str] = []

        for sentence in sentences:
            sentence_matched = False
            for category, patterns in BROAD_PATTERNS.items():
                for pattern in patterns:
                    if re.search(pattern, sentence, flags=re.IGNORECASE | re.DOTALL):
                        category_counts[category] += 1
                        phrase_counts[pattern] += 1
                        sentence_matched = True
            if sentence_matched and len(matched_sentences) < 8:
                matched_sentences.append(sentence[:500])

        categories = ",".join(
            f"{name}:{count}"
            for name, count in category_counts.most_common()
        ) or "none"

        print(
            "BLINDSPOT | "
            f"company={company} | chars={len(text)} | sentences={len(sentences)} | "
            f"matched_sentences={len(matched_sentences)} | categories={categories}"
        )

        for index, sentence in enumerate(matched_sentences, start=1):
            print(
                f"BLINDSPOT_SAMPLE | company={company} | n={index} | sentence={sentence}"
            )


if __name__ == "__main__":
    main()
