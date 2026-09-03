import spacy

from .domain_matcher import DomainMatcher
from .domain_rules import DOMAIN_RULES
from .models import ExtractedEntity


class EntityExtractor:
    def __init__(self, model_name: str = "en_core_web_sm") -> None:
        self.nlp = spacy.load(model_name)
        self.domain_matcher = DomainMatcher(self.nlp)

    def extract(self, text: str) -> list[ExtractedEntity]:
        if not text.strip():
            return []

        doc = self.nlp(text)
        domain_matches = self.domain_matcher.match(doc)

        entities: list[ExtractedEntity] = []
        seen_spans: set[tuple[int, int]] = set()

        # 1. spaCy-detected entities
        for ent in doc.ents:
            domain_type = DOMAIN_RULES.get(ent.label_)

            matched_domain_type = domain_matches.get((ent.start, ent.end))

            if matched_domain_type is not None:
                domain_type = matched_domain_type

            entities.append(
                ExtractedEntity(
                    text=ent.text,
                    nlp_label=ent.label_,
                    domain_type=domain_type,
                    start_char=ent.start_char,
                    end_char=ent.end_char,
                )
            )

            seen_spans.add((ent.start, ent.end))

        # 2. Domain entities spaCy missed
        for (start, end), domain_type in domain_matches.items():
            if (start, end) in seen_spans:
                continue

            span = doc[start:end]

            entities.append(
                ExtractedEntity(
                    text=span.text,
                    nlp_label="DOMAIN_RULE",
                    domain_type=domain_type,
                    start_char=span.start_char,
                    end_char=span.end_char,
                )
            )

        return sorted(
            entities,
            key=lambda entity: entity.start_char,
            )
    def extract_long_text(
        self,
        text: str,
        chunk_size: int = 50_000,
    ) -> list[ExtractedEntity]:
        if not text.strip():
            return []

        all_entities: list[ExtractedEntity] = []

        for offset in range(0, len(text), chunk_size):
            chunk = text[offset:offset + chunk_size]

            chunk_entities = self.extract(chunk)

            for entity in chunk_entities:
                all_entities.append(
                    ExtractedEntity(
                        text=entity.text,
                        nlp_label=entity.nlp_label,
                        domain_type=entity.domain_type,
                        start_char=entity.start_char + offset,
                        end_char=entity.end_char + offset,
                        confidence=entity.confidence,
                    )
                )

        return sorted(
            all_entities,
            key=lambda entity: entity.start_char,
        )