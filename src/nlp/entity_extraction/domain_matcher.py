from spacy.language import Language
from spacy.matcher import PhraseMatcher

from .aliases import DOMAIN_ALIASES
from .seed_loader import SeedVocabularyLoader


class DomainMatcher:
    def __init__(self, nlp: Language) -> None:
        self.matcher = PhraseMatcher(
            nlp.vocab,
            attr="LOWER",
        )

        loader = SeedVocabularyLoader()

        # Companies
        self._add_patterns(
            nlp,
            "Company",
            loader.load_companies(),
        )

        # Facilities
        self._add_patterns(
            nlp,
            "Facility",
            loader.load_facilities(),
        )

        # Countries / locations
        self._add_patterns(
            nlp,
            "Location",
            loader.load_countries(),
        )

        # Products
        self._add_patterns(
            nlp,
            "Product",
            loader.load_products(),
        )

        # Materials
        self._add_patterns(
            nlp,
            "Material",
            loader.load_materials(),
        )

        # Common aliases / abbreviations
        for domain_type, aliases in DOMAIN_ALIASES.items():
            self._add_patterns(
                nlp,
                domain_type,
                aliases,
            )

    def _add_patterns(
        self,
        nlp: Language,
        domain_type: str,
        patterns: list[str],
    ) -> None:
        docs = [
            nlp.make_doc(pattern)
            for pattern in patterns
        ]

        self.matcher.add(
            domain_type,
            docs,
        )

    def match(
        self,
        doc,
    ) -> dict[tuple[int, int], str]:
        raw_matches = self.matcher(doc)

        # Longest matches first
        raw_matches = sorted(
            raw_matches,
            key=lambda match: match[2] - match[1],
            reverse=True,
        )

        accepted: list[tuple[int, int, str]] = []
        occupied_tokens: set[int] = set()

        for match_id, start, end in raw_matches:
            token_range = set(range(start, end))

            # Skip overlaps with an already accepted longer span
            if token_range & occupied_tokens:
                continue

            domain_type = doc.vocab.strings[match_id]

            accepted.append(
                (
                    start,
                    end,
                    domain_type,
                )
            )

            occupied_tokens.update(token_range)

        return {
            (start, end): domain_type
            for start, end, domain_type in accepted
        }