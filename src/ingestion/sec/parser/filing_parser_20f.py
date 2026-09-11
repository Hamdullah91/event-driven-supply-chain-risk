from __future__ import annotations

import re

from .filing_parser import SEC10KParser
from .models import FilingMetadata, FilingParagraph, FilingSection, ParsedFiling


ITEM_PATTERN_20F = re.compile(
    r"\bITEM\s*(3|4|5)\b\s*[.\-:]?",
    re.IGNORECASE,
)

RELEVANT_ITEMS_20F = {"3", "4", "5"}
SECTION_TITLES_20F = {
    "3": "Key Information and Risk Factors",
    "4": "Information on the Company",
    "5": "Operating and Financial Review and Prospects",
}
MIN_SECTION_CHARS_20F = {
    "3": 1000,
    "4": 1000,
    "5": 1000,
}


class SEC20FParser(SEC10KParser):
    """Parse supply-chain-relevant sections from SEC Form 20-F filings.

    Form 20-F uses a different item structure from Form 10-K. We retain
    Items 3, 4, and 5 because they contain risk factors, business/sourcing
    disclosures, facilities, and operating-review material used by the
    downstream supply-chain extractor.
    """

    @staticmethod
    def extract_sections(text: str) -> dict[str, str]:
        matches = list(ITEM_PATTERN_20F.finditer(text))
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
            minimum = MIN_SECTION_CHARS_20F.get(item, 100)
            plausible = [
                candidate
                for candidate in item_candidates
                if len(candidate) >= minimum
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
            if item in RELEVANT_ITEMS_20F
        }

    @classmethod
    def build_paragraph_objects_20f(
        cls,
        section: str,
        section_title: str,
        paragraphs: list[str],
    ) -> list[FilingParagraph]:
        results: list[FilingParagraph] = []
        for index, paragraph in enumerate(paragraphs):
            keywords = cls.find_supply_chain_keywords(paragraph)
            results.append(
                FilingParagraph(
                    paragraph_id=f"20F-{section}-{index}",
                    section=section,
                    section_title=section_title,
                    paragraph_index=index,
                    text=paragraph,
                    relevant=bool(keywords),
                    matched_keywords=tuple(keywords),
                )
            )
        return results

    @classmethod
    def build_section_objects_20f(
        cls,
        sections: dict[str, str],
    ) -> list[FilingSection]:
        results: list[FilingSection] = []
        for item, section_text in sections.items():
            section_title = SECTION_TITLES_20F.get(item, f"Item {item}")
            paragraphs = cls.split_paragraphs(section_text)
            paragraph_objects = cls.build_paragraph_objects_20f(
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
        if metadata.form.upper() != "20-F":
            raise ValueError(
                f"SEC20FParser requires form 20-F, got {metadata.form!r}"
            )

        text = self.html_to_text(html)
        sections = self.extract_sections(text)
        relevant_sections = self.filter_relevant_sections(sections)
        section_objects = self.build_section_objects_20f(relevant_sections)

        return ParsedFiling(
            metadata=metadata,
            sections=tuple(section_objects),
        )
