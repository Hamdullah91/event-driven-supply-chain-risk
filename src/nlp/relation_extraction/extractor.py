from __future__ import annotations

from collections.abc import Iterable

from .models import RelationCandidate


OBJECT_TYPES = {
    "ORG": "Company",
    "FAC": "Facility",
    "GPE": "Location",
    "LOC": "Location",
    "PRODUCT": "Product",
}

DEPENDENCY_LEMMAS = {"depend", "rely", "source", "purchase", "procure", "obtain", "outsource"}
SUPPLY_LEMMAS = {"supply", "provide", "deliver"}
PRODUCTION_LEMMAS = {"produce", "manufacture", "fabricate", "assemble", "build"}
USE_LEMMAS = {"use", "utilize"}
OPERATE_LEMMAS = {"operate"}
OWN_LEMMAS = {"own"}

FILING_REFERENCES = {"we", "us", "our", "ours", "ourselves", "company", "the company"}
RELATIVE_PRONOUNS = {"who", "which", "that"}


class RelationExtractor:
    """Conservative entity-first SEC relation extraction.

    The extractor starts from typed entity mentions and only emits candidates
    for relation-specific dependency structures. Entity resolution and graph
    ontology validation remain downstream responsibilities.
    """

    def __init__(self, nlp):
        self.nlp = nlp

    @staticmethod
    def _entity_for_token(token):
        for ent in token.doc.ents:
            if ent.start <= token.i < ent.end:
                return ent
        return None

    @staticmethod
    def _graph_type(ent) -> str | None:
        if ent is None:
            return None
        return OBJECT_TYPES.get(ent.label_)

    @classmethod
    def _mention(cls, token) -> tuple[str, str | None]:
        ent = cls._entity_for_token(token)
        if ent is not None:
            return ent.text, cls._graph_type(ent)
        return token.text, None

    @staticmethod
    def _children(token, deps: set[str]) -> list:
        return [child for child in token.children if child.dep_ in deps]

    @staticmethod
    def _prep_objects(token, prepositions: set[str]) -> list:
        objects = []
        for child in token.children:
            if child.dep_ not in {"prep", "agent"}:
                continue
            if child.lemma_.lower() not in prepositions and child.text.lower() not in prepositions:
                continue
            objects.extend(
                grandchild
                for grandchild in child.children
                if grandchild.dep_ == "pobj"
            )
        return objects

    @classmethod
    def _subject_mentions(cls, verb) -> list:
        subjects = cls._children(verb, {"nsubj", "nsubjpass"})

        # Relative clauses are only accepted when their local antecedent is a
        # typed Company. This prevents generic noun phrases such as
        # "systems, which supply data..." from leaking into the graph.
        if verb.dep_ == "relcl":
            antecedent = verb.head
            antecedent_ent = cls._entity_for_token(antecedent)
            antecedent_is_company = (
                antecedent_ent is not None
                and cls._graph_type(antecedent_ent) == "Company"
            )
            if not antecedent_is_company:
                return []

            relative_subjects = [
                subject
                for subject in subjects
                if subject.lemma_.lower() in RELATIVE_PRONOUNS
                or subject.text.lower() in RELATIVE_PRONOUNS
            ]
            if relative_subjects or not subjects:
                return [antecedent]

            return []

        return subjects

    @classmethod
    def _direct_objects(cls, verb) -> list:
        return cls._children(verb, {"dobj", "obj", "attr", "dative"})

    @classmethod
    def _typed_entities_in_subtree(cls, token) -> list[tuple[str, str]]:
        indexes = {item.i for item in token.subtree}
        values: list[tuple[str, str]] = []
        for ent in token.doc.ents:
            graph_type = cls._graph_type(ent)
            if graph_type is None:
                continue
            if indexes.intersection(range(ent.start, ent.end)):
                values.append((ent.text, graph_type))
        return values

    @classmethod
    def _object_mentions(cls, tokens: Iterable) -> list[tuple[str, str | None]]:
        values: list[tuple[str, str | None]] = []
        for token in tokens:
            typed = cls._typed_entities_in_subtree(token)
            if typed:
                values.extend(typed)
            else:
                values.append(cls._mention(token))
        return values

    @staticmethod
    def _is_filing_reference(text: str) -> bool:
        return " ".join(text.lower().split()) in FILING_REFERENCES

    @classmethod
    def _emit(
        cls,
        *,
        sentence,
        subjects: list,
        objects: list[tuple[str, str | None]],
        relationship: str,
        pattern_id: str,
        voice: str,
        extraction_confidence: float,
    ) -> list[RelationCandidate]:
        candidates: list[RelationCandidate] = []
        for subject_token in subjects:
            subject, subject_type = cls._mention(subject_token)
            attribution = 0.98 if cls._is_filing_reference(subject) else 0.92 if subject_type == "Company" else 0.70
            for object_text, object_type in objects:
                candidates.append(
                    RelationCandidate(
                        subject=subject,
                        relationship=relationship,
                        object=object_text,
                        source_sentence=sentence.text.strip(),
                        pattern_id=pattern_id,
                        voice=voice,
                        subject_type=subject_type,
                        object_type=object_type,
                        extraction_confidence=extraction_confidence,
                        attribution_confidence=attribution,
                    )
                )
        return candidates

    @classmethod
    def _emit_explicit(
        cls,
        *,
        sentence,
        subject_text: str,
        subject_type: str | None,
        object_text: str,
        object_type: str | None,
        relationship: str,
        pattern_id: str,
        extraction_confidence: float,
    ) -> RelationCandidate:
        attribution = 0.92 if subject_type == "Company" else 0.85
        return RelationCandidate(
            subject=subject_text,
            relationship=relationship,
            object=object_text,
            source_sentence=sentence.text.strip(),
            pattern_id=pattern_id,
            voice="passive",
            subject_type=subject_type,
            object_type=object_type,
            extraction_confidence=extraction_confidence,
            attribution_confidence=attribution,
        )

    def extract(self, text: str) -> list[RelationCandidate]:
        doc = self.nlp(text)
        candidates: list[RelationCandidate] = []

        for sentence in doc.sents:
            for verb in sentence:
                if verb.pos_ != "VERB":
                    continue

                lemma = verb.lemma_.lower()
                subjects = self._subject_mentions(verb)
                if not subjects:
                    continue

                passive = any(subject.dep_ == "nsubjpass" for subject in subjects)

                if lemma in DEPENDENCY_LEMMAS:
                    if passive:
                        continue
                    objects = self._object_mentions(
                        self._prep_objects(verb, {"on", "upon", "from", "to"})
                    )
                    if objects:
                        candidates.extend(self._emit(
                            sentence=sentence, subjects=subjects, objects=objects,
                            relationship="DEPENDS_ON", pattern_id=f"dependency_{lemma}_prep",
                            voice="active", extraction_confidence=0.94,
                        ))

                elif lemma in SUPPLY_LEMMAS:
                    if passive:
                        agents = self._object_mentions(self._prep_objects(verb, {"by"}))
                        supplied = [self._mention(subject) for subject in subjects]
                        for agent_text, agent_type in agents:
                            if agent_type != "Company":
                                continue
                            for supplied_text, supplied_type in supplied:
                                if supplied_type != "Company":
                                    continue
                                candidates.append(self._emit_explicit(
                                    sentence=sentence,
                                    subject_text=agent_text,
                                    subject_type=agent_type,
                                    object_text=supplied_text,
                                    object_type=supplied_type,
                                    relationship="SUPPLIES",
                                    pattern_id=f"supply_{lemma}_passive_by",
                                    extraction_confidence=0.97,
                                ))
                    else:
                        destinations = self._object_mentions(
                            self._prep_objects(verb, {"to", "for"})
                        )
                        if destinations:
                            candidates.extend(self._emit(
                                sentence=sentence, subjects=subjects, objects=destinations,
                                relationship="SUPPLIES", pattern_id=f"supply_{lemma}_destination",
                                voice="active", extraction_confidence=0.93,
                            ))

                elif lemma in PRODUCTION_LEMMAS:
                    if passive:
                        agents = self._object_mentions(self._prep_objects(verb, {"by"}))
                        products = [self._mention(subject) for subject in subjects]
                        for agent_text, agent_type in agents:
                            if agent_type != "Company":
                                continue
                            for product_text, product_type in products:
                                if product_type != "Product":
                                    continue
                                candidates.append(self._emit_explicit(
                                    sentence=sentence,
                                    subject_text=agent_text,
                                    subject_type=agent_type,
                                    object_text=product_text,
                                    object_type=product_type,
                                    relationship="PRODUCES",
                                    pattern_id=f"production_{lemma}_passive_by",
                                    extraction_confidence=0.97,
                                ))
                    else:
                        objects = self._object_mentions(self._direct_objects(verb))
                        objects = [value for value in objects if value[1] == "Product"]
                        if objects:
                            candidates.extend(self._emit(
                                sentence=sentence, subjects=subjects, objects=objects,
                                relationship="PRODUCES", pattern_id=f"production_{lemma}_product",
                                voice="active", extraction_confidence=0.95,
                            ))

                elif lemma in USE_LEMMAS:
                    if passive:
                        continue
                    objects = self._object_mentions(self._direct_objects(verb))
                    objects = [value for value in objects if value[1] in {"Product", None}]
                    if objects:
                        candidates.extend(self._emit(
                            sentence=sentence, subjects=subjects, objects=objects,
                            relationship="USES", pattern_id=f"use_{lemma}_object",
                            voice="active", extraction_confidence=0.88,
                        ))

                elif lemma in OPERATE_LEMMAS | OWN_LEMMAS:
                    if passive:
                        continue
                    objects = self._object_mentions(self._direct_objects(verb))
                    objects = [value for value in objects if value[1] == "Facility"]
                    if objects:
                        relationship = "OPERATES" if lemma in OPERATE_LEMMAS else "OWNS"
                        candidates.extend(self._emit(
                            sentence=sentence, subjects=subjects, objects=objects,
                            relationship=relationship, pattern_id=f"facility_{lemma}",
                            voice="active", extraction_confidence=0.96,
                        ))

        unique: list[RelationCandidate] = []
        seen: set[tuple] = set()
        for candidate in candidates:
            key = (
                candidate.subject,
                candidate.relationship,
                candidate.object,
                candidate.source_sentence,
                candidate.pattern_id,
            )
            if key not in seen:
                seen.add(key)
                unique.append(candidate)
        return unique
