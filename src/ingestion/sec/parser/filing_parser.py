from __future__ import annotations

import re

import warnings

from bs4 import BeautifulSoup, XMLParsedAsHTMLWarning

warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)

from .models import (
    FilingMetadata,
    FilingParagraph,
    FilingSection,
    ParsedFiling,
)

# SEC filings are inconsistent about whether Item headings start on their own
# line.  Match headings inline, then reject table-of-contents/cross-reference
# occurrences by requiring a plausible section body.
ITEM_PATTERN = re.compile(
    r"\bITEM\s*"
    r"(1A|1B|1C|7A|9A|9B|9C|10|11|12|13|14|15|16|1|2|3|4|5|6|7|8|9)"
    r"\b\s*[.\-:]?",
    re.IGNORECASE,
)

RELEVANT_ITEMS = {
    "1",
    "1A",
    "2",
    "7",
}
SUPPLY_CHAIN_KEYWORDS = (
    "supplier",
    "suppliers",
    "supply chain",
    "vendor",
    "vendors",
    "foundry",
    "foundries",
    "manufacturing",
    "factory",
    "factories",
    "facility",
    "facilities",
    "raw material",
    "raw materials",
    "component",
    "components",
    "semiconductor",
    "semiconductors",
    "shortage",
    "shortages",
    "disruption",
    "disruptions",
    "dependency",
    "dependencies",
    "depend on",
    "depends on",
    "rely on",
    "relies on",
    "logistics",
    "shipping",
    "procurement",
    "sourcing",
)
SECTION_TITLES = {
    "1": "Business",
    "1A": "Risk Factors",
    "2": "Properties",
    "7": "Management's Discussion and Analysis",
}

# A real 10-K Item 1/1A/7 body is normally far larger than a table-of-contents
# entry.  Item 2 can legitimately be shorter, so use a smaller floor there.
MIN_SECTION_CHARS = {
    "1": 1000,
    "1A": 1000,
    "2": 250,
    "7": 1000,
}
DEFAULT_MIN_SECTION_CHARS = 100


class SEC10KParser:
    """
    Converts SEC 10-K HTML into clean normalized text.
    """

    @staticmethod
    def html_to_text(html: str) -> str:
        if not html.strip():
            raise ValueError("SEC filing HTML is empty")

        soup = BeautifulSoup(html, "lxml")

        for element in soup(
            [
                "script",
                "style",
                "noscript",
                "svg",
            ]
        ):
            element.decompose()

        text = soup.get_text(separator="\n")
        text = text.replace("\xa0", " ")
        text = re.sub(r"[ \t]+", " ", text)
        text = re.sub(r" *\n *", "\n", text)
        text = re.sub(r"\n{3,}", "\n\n", text)

        return text.strip()

    @staticmethod
    def extract_sections(text: str) -> dict[str, str]:
        matches = list(ITEM_PATTERN.finditer(text))

        if not matches:
            return {}

        candidates: dict[str, list[str]] = {}

        for index, match in enumerate(matches):
            item = match.group(1).upper()
            start = match.end()

            # A section ends at the next *different* Item heading. Repeated
            # occurrences of the same heading are kept as separate candidates;
            # the longest plausible body wins below.
            end = len(text)
            for next_match in matches[index + 1 :]:
                if next_match.group(1).upper() != item:
                    end = next_match.start()
                    break

            section_text = text[start:end].strip()

            if not section_text:
                continue

            candidates.setdefault(item, []).append(section_text)

        sections: dict[str, str] = {}

        for item, item_candidates in candidates.items():
            minimum = MIN_SECTION_CHARS.get(
                item,
                DEFAULT_MIN_SECTION_CHARS,
            )
            plausible = [
                candidate
                for candidate in item_candidates
                if len(candidate) >= minimum
            ]

            # Prefer a plausible real section. If none passes the floor, keep
            # the longest candidate for backwards compatibility and diagnostics.
            pool = plausible or item_candidates
            sections[item] = max(pool, key=len)

        return sections

    @staticmethod
    def filter_relevant_sections(
        sections: dict[str, str],
    ) -> dict[str, str]:
        return {
            item: text
            for item, text in sections.items()
            if item in RELEVANT_ITEMS
        }

    @staticmethod
    def split_paragraphs(section_text: str) -> list[str]:
        raw_paragraphs = re.split(
            r"\n+",
            section_text,
        )

        paragraphs: list[str] = []

        for paragraph in raw_paragraphs:
            cleaned = re.sub(
                r"\s+",
                " ",
                paragraph,
            ).strip()

            if not cleaned:
                continue

            paragraphs.append(cleaned)

        return paragraphs

    @staticmethod
    def find_supply_chain_keywords(
        paragraph: str,
    ) -> list[str]:
        paragraph_lower = paragraph.lower()

        return [
            keyword
            for keyword in SUPPLY_CHAIN_KEYWORDS
            if keyword in paragraph_lower
        ]

    @staticmethod
    def build_paragraph_objects(
        section: str,
        section_title: str,
        paragraphs: list[str],
    ) -> list[FilingParagraph]:
        results: list[FilingParagraph] = []

        for index, paragraph in enumerate(paragraphs):
            keywords = SEC10KParser.find_supply_chain_keywords(
                paragraph
            )

            paragraph_id = f"{section}-{index}"

            results.append(
                FilingParagraph(
                    paragraph_id=paragraph_id,
                    section=section,
                    section_title=section_title,
                    paragraph_index=index,
                    text=paragraph,
                    relevant=bool(keywords),
                    matched_keywords=tuple(keywords),
                )
            )

        return results

    @staticmethod
    def build_section_objects(
        sections: dict[str, str],
    ) -> list[FilingSection]:
        results: list[FilingSection] = []

        for item, section_text in sections.items():
            section_title = SECTION_TITLES.get(
                item,
                f"Item {item}",
            )

            paragraphs = SEC10KParser.split_paragraphs(
                section_text
            )

            paragraph_objects = (
                SEC10KParser.build_paragraph_objects(
                    section=item,
                    section_title=section_title,
                    paragraphs=paragraphs,
                )
            )

            results.append(
                FilingSection(
                    item=item,
                    title=section_title,
                    text=section_text,
                    paragraphs=tuple(paragraph_objects),
                )
            )

        return results

    def parse(
        self,
        html: str,
        metadata: FilingMetadata,
    ) -> ParsedFiling:
        text = self.html_to_text(html)
        sections = self.extract_sections(text)
        relevant_sections = self.filter_relevant_sections(
            sections
        )
        section_objects = self.build_section_objects(
            relevant_sections
        )

        return ParsedFiling(
            metadata=metadata,
            sections=tuple(section_objects),
        )
