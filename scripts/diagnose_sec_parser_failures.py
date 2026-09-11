from __future__ import annotations

import json
from pathlib import Path

from scripts.preprocess_sec import RAW_SEC_ROOT
from src.ingestion.sec.parser.filing_parser import ITEM_PATTERN, SEC10KParser


TARGET_COMPANIES = {
    "GE Aerospace",
    "Intel Corporation",
    "Honeywell International Inc.",
}


def _load_metadata(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _candidate_lengths(text: str) -> dict[str, list[int]]:
    matches = list(ITEM_PATTERN.finditer(text))
    candidates: dict[str, list[int]] = {}

    for index, match in enumerate(matches):
        item = match.group(1).upper()
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        section_text = text[start:end].strip()
        if section_text:
            candidates.setdefault(item, []).append(len(section_text))

    return candidates


def main() -> None:
    parser = SEC10KParser()
    found = 0

    for metadata_path in sorted(RAW_SEC_ROOT.rglob("metadata.json")):
        metadata = _load_metadata(metadata_path)
        company = metadata.get("company_name", "")

        if company not in TARGET_COMPANIES:
            continue

        found += 1
        filing_dir = metadata_path.parent
        html_path = filing_dir / "10-k.htm"
        html = html_path.read_text(encoding="utf-8", errors="ignore")
        text = parser.html_to_text(html)
        matches = list(ITEM_PATTERN.finditer(text))
        sections = parser.extract_sections(text)
        relevant = parser.filter_relevant_sections(sections)
        candidate_lengths = _candidate_lengths(text)

        print(
            "PARSER_DIAG | "
            f"company={company} | "
            f"raw_html_chars={len(html)} | "
            f"plain_text_chars={len(text)} | "
            f"item_matches={len(matches)} | "
            f"items={','.join(match.group(1).upper() for match in matches) or 'none'}"
        )

        for item in ("1", "1A", "2", "7"):
            lengths = candidate_lengths.get(item, [])
            chosen = len(relevant.get(item, ""))
            print(
                "PARSER_ITEM | "
                f"company={company} | "
                f"item={item} | "
                f"candidates={len(lengths)} | "
                f"candidate_lengths={','.join(str(length) for length in lengths) or 'none'} | "
                f"chosen_chars={chosen}"
            )

        # Show normalized snippets around detected ITEM headings without dumping the filing.
        for index, match in enumerate(matches[:12]):
            start = max(0, match.start() - 80)
            end = min(len(text), match.end() + 120)
            snippet = " ".join(text[start:end].split())
            print(
                "PARSER_HEADING | "
                f"company={company} | "
                f"index={index} | item={match.group(1).upper()} | "
                f"snippet={snippet[:220]}"
            )

    print(f"PARSER_DIAG_SUMMARY | targets_found={found}")


if __name__ == "__main__":
    main()
