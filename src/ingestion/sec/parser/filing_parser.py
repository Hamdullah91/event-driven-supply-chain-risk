from __future__ import annotations

import re
import warnings

from bs4 import BeautifulSoup, NavigableString, XMLParsedAsHTMLWarning

warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)

from .models import (
    FilingMetadata,
    FilingParagraph,
    FilingSection,
    ParsedFiling,
)

ITEM_PATTERN = re.compile(
    r"\bITEM\s*"
    r"(1A|1B|1C|7A|9A|9B|9C|10|11|12|13|14|15|16|1|2|3|4|5|6|7|8|9)"
    r"\b\s*[.\-:]?",
    re.IGNORECASE,
)

RELEVANT_ITEMS = {"1", "1A", "2", "7"}

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

SECTION_TITLE_ALIASES = {
    "1": (
        "business",
        "our business",
        "about honeywell",
        "business overview and environment",
    ),
    "1A": ("risk factors",),
    "2": ("properties",),
    "7": (
        "management's discussion and analysis",
        "management’s discussion and analysis",
        "management's discussion and analysis of financial condition and results of operations",
        "management’s discussion and analysis of financial condition and results of operations",
        "md&a",
    ),
}

MIN_SECTION_CHARS = {
    "1": 1000,
    "1A": 1000,
    "2": 250,
    "7": 1000,
}
DEFAULT_MIN_SECTION_CHARS = 100


def _normalize_label(value: str) -> str:
    value = value.replace("\xa0", " ").strip().lower()
    value = value.rstrip(".:")
    value = re.sub(r"\s+", " ", value)
    return value


class SEC10KParser:
    """Converts SEC 10-K HTML into normalized relevant Item sections."""

    @staticmethod
    def _make_soup(html: str) -> BeautifulSoup:
        if not html.strip():
            raise ValueError("SEC filing HTML is empty")

        soup = BeautifulSoup(html, "lxml")
        for element in soup(["script", "style", "noscript", "svg"]):
            element.decompose()
        return soup

    @classmethod
    def html_to_text(cls, html: str) -> str:
        soup = cls._make_soup(html)
        text = soup.get_text(separator="\n")
        text = text.replace("\xa0", " ")
        text = re.sub(r"[ \t]+", " ", text)
        text = re.sub(r" *\n *", "\n", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()

    @staticmethod
    def _item_for_title(text: str) -> str | None:
        normalized = _normalize_label(text)

        for item, aliases in SECTION_TITLE_ALIASES.items():
            for alias in aliases:
                if normalized == alias or normalized.startswith(alias + " "):
                    return item

        return None

    @classmethod
    def _anchor_targets(cls, soup: BeautifulSoup) -> dict[str, list[object]]:
        targets: dict[str, list[object]] = {item: [] for item in RELEVANT_ITEMS}

        for link in soup.find_all("a", href=True):
            href = str(link.get("href", ""))
            if not href.startswith("#"):
                continue

            item = cls._item_for_title(link.get_text(" ", strip=True))
            if item is None:
                continue

            target_id = href[1:]
            if not target_id:
                continue

            target = soup.find(id=target_id) or soup.find(attrs={"name": target_id})
            if target is not None:
                targets[item].append(target)

        return targets

    @classmethod
    def _title_targets(cls, soup: BeautifulSoup) -> dict[str, list[object]]:
        targets: dict[str, list[object]] = {item: [] for item in RELEVANT_ITEMS}

        for tag in soup.find_all(["div", "span", "td", "p", "b", "strong", "h1", "h2", "h3", "h4"]):
            text = tag.get_text(" ", strip=True)
            if not text or len(text) > 180:
                continue

            item = cls._item_for_title(text)
            if item is not None:
                targets[item].append(tag)

        return targets

    @staticmethod
    def _extract_between(start, stop_nodes: set[int]) -> str:
        pieces: list[str] = []

        for element in start.next_elements:
            if element is start:
                continue

            if getattr(element, "name", None) is not None and id(element) in stop_nodes:
                break

            if not isinstance(element, NavigableString):
                continue

            parent_name = getattr(element.parent, "name", "")
            if parent_name in {"script", "style", "noscript", "svg"}:
                continue

            text = " ".join(str(element).split())
            if text:
                pieces.append(text)

        return " ".join(pieces).strip()

    @classmethod
    def extract_sections_from_html(cls, html: str) -> dict[str, str]:
        soup = cls._make_soup(html)

        anchor_targets = cls._anchor_targets(soup)
        title_targets = cls._title_targets(soup)

        all_candidates: dict[str, list[object]] = {item: [] for item in RELEVANT_ITEMS}
        for item in RELEVANT_ITEMS:
            seen: set[int] = set()
            for node in [*anchor_targets[item], *title_targets[item]]:
                marker = id(node)
                if marker not in seen:
                    seen.add(marker)
                    all_candidates[item].append(node)

        boundary_nodes = {
            id(node)
            for nodes in all_candidates.values()
            for node in nodes
        }

        sections: dict[str, str] = {}

        for item, nodes in all_candidates.items():
            candidates: list[str] = []
            minimum = MIN_SECTION_CHARS.get(item, DEFAULT_MIN_SECTION_CHARS)

            for node in nodes:
                body = cls._extract_between(
                    node,
                    boundary_nodes - {id(node)},
                )
                if body:
                    candidates.append(body)

            plausible = [candidate for candidate in candidates if len(candidate) >= minimum]
            if plausible:
                sections[item] = max(plausible, key=len)

        return sections

    @staticmethod
    def extract_sections(text: str) -> dict[str, str]:
        matches = list(ITEM_PATTERN.finditer(text))
        if not matches:
            return {}

        candidates: dict[str, list[str]] = {}

        for index, match in enumerate(matches):
            item = match.group(1).upper()
            start = match.end()
            end = len(text)

            for next_match in matches[index + 1 :]:
                if next_match.group(1).upper() != item:
                    end = next_match.start()
                    break

            section_text = text[start:end].strip()
            if section_text:
                candidates.setdefault(item, []).append(section_text)

        sections: dict[str, str] = {}

        for item, item_candidates in candidates.items():
            minimum = MIN_SECTION_CHARS.get(item, DEFAULT_MIN_SECTION_CHARS)
            plausible = [
                candidate for candidate in item_candidates if len(candidate) >= minimum
            ]
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
        raw_paragraphs = re.split(r"\n+", section_text)
        paragraphs: list[str] = []

        for paragraph in raw_paragraphs:
            cleaned = re.sub(r"\s+", " ", paragraph).strip()
            if cleaned:
                paragraphs.append(cleaned)

        return paragraphs

    @staticmethod
    def find_supply_chain_keywords(paragraph: str) -> list[str]:
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
            keywords = SEC10KParser.find_supply_chain_keywords(paragraph)
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
    def build_section_objects(sections: dict[str, str]) -> list[FilingSection]:
        results: list[FilingSection] = []

        for item, section_text in sections.items():
            section_title = SECTION_TITLES.get(item, f"Item {item}")
            paragraphs = SEC10KParser.split_paragraphs(section_text)
            paragraph_objects = SEC10KParser.build_paragraph_objects(
                section=item,
                section_title=section_title,
                paragraphs=paragraphs,
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
        html_sections = self.extract_sections_from_html(html)

        if len(html_sections) < len(RELEVANT_ITEMS):
            text = self.html_to_text(html)
            text_sections = self.extract_sections(text)
            for item, section_text in text_sections.items():
                html_sections.setdefault(item, section_text)

        relevant_sections = self.filter_relevant_sections(html_sections)
        section_objects = self.build_section_objects(relevant_sections)

        return ParsedFiling(
            metadata=metadata,
            sections=tuple(section_objects),
        )
