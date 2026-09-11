from __future__ import annotations

import json
import re
from pathlib import Path

from bs4 import BeautifulSoup

from scripts.preprocess_sec import RAW_SEC_ROOT


TARGET_COMPANIES = {
    "GE Aerospace",
    "Intel Corporation",
    "Honeywell International Inc.",
}

TITLE_PATTERNS = {
    "1": re.compile(r"\b(?:business|about honeywell|description of business)\b", re.I),
    "1A": re.compile(r"\brisk factors\b", re.I),
    "2": re.compile(r"\bproperties\b", re.I),
    "7": re.compile(r"\bmanagement(?:['’]s)? discussion|md&a\b", re.I),
}


def _load_metadata(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _norm(text: str) -> str:
    return " ".join(text.split())


def main() -> None:
    found = 0

    for metadata_path in sorted(RAW_SEC_ROOT.rglob("metadata.json")):
        metadata = _load_metadata(metadata_path)
        company = metadata.get("company_name", "")
        if company not in TARGET_COMPANIES:
            continue

        found += 1
        html_path = metadata_path.parent / "10-k.htm"
        html = html_path.read_text(encoding="utf-8", errors="ignore")
        soup = BeautifulSoup(html, "lxml")

        ids = {tag.get("id") for tag in soup.find_all(attrs={"id": True})}
        names = {tag.get("name") for tag in soup.find_all(attrs={"name": True})}

        internal_links = []
        for link in soup.find_all("a", href=True):
            href = str(link.get("href", ""))
            text = _norm(link.get_text(" ", strip=True))
            if href.startswith("#"):
                target = href[1:]
                internal_links.append((text, href, target in ids or target in names))

        print(
            "HTML_STRUCTURE | "
            f"company={company} | ids={len(ids)} | names={len(names)} | "
            f"internal_links={len(internal_links)}"
        )

        emitted = 0
        for text, href, target_exists in internal_links:
            if not text:
                continue
            if re.search(r"\bitem\s*(1a|1|2|7)\b", text, re.I) or any(
                pattern.search(text)
                for pattern in TITLE_PATTERNS.values()
            ):
                print(
                    "HTML_LINK | "
                    f"company={company} | text={text[:180]} | href={href[:120]} | "
                    f"target_exists={target_exists}"
                )
                emitted += 1
                if emitted >= 20:
                    break

        # Search visible HTML elements for likely real section-title text and
        # show their tag/id plus nearby container text. This reveals filings
        # where the body section is titled "About Honeywell" or similar instead
        # of repeating the literal Item number.
        for item, pattern in TITLE_PATTERNS.items():
            matches = []
            for tag in soup.find_all(["div", "p", "span", "td", "a"]):
                text = _norm(tag.get_text(" ", strip=True))
                if not text or len(text) > 240:
                    continue
                if pattern.search(text):
                    matches.append(tag)

            print(
                "HTML_TITLE_SUMMARY | "
                f"company={company} | item={item} | matches={len(matches)}"
            )

            for index, tag in enumerate(matches[:8]):
                text = _norm(tag.get_text(" ", strip=True))
                tag_id = tag.get("id") or ""
                tag_name = tag.get("name") or ""
                parent = tag.parent
                parent_id = parent.get("id") if parent else ""
                snippet = _norm(parent.get_text(" ", strip=True))[:260] if parent else text[:260]
                print(
                    "HTML_TITLE | "
                    f"company={company} | item={item} | index={index} | "
                    f"tag={tag.name} | id={tag_id} | name={tag_name} | "
                    f"parent_id={parent_id or ''} | text={text[:160]} | snippet={snippet}"
                )

    print(f"HTML_STRUCTURE_SUMMARY | targets_found={found}")


if __name__ == "__main__":
    main()
