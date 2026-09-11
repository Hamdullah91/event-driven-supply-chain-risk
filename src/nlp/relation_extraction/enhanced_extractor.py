from __future__ import annotations

from .extractor import DEPENDENCY_LEMMAS, PRODUCTION_LEMMAS, RelationExtractor as BaseRelationExtractor
from .models import RelationCandidate


_NOMINAL_PRODUCTION_LEMMAS = {"manufacture", "production", "assembly"}
_FACILITY_HEADS = {"facility", "plant", "factory", "fab", "mine", "warehouse"}


class RelationExtractor(BaseRelationExtractor):
    """Production extractor plus conservative recall-recovery patterns.

    These fallbacks only fire on explicit SEC dependency, production, or
    ownership syntax. They intentionally avoid generic customer/category
    phrases so improved recall does not create low-quality graph nodes.
    """

    @staticmethod
    def _span_text(token) -> str:
        items = list(token.subtree)
        if not items:
            return token.text
        start = min(item.i for item in items)
        end = max(item.i for item in items) + 1
        return token.doc[start:end].text.strip()

    @staticmethod
    def _subject_from_ancestor(verb):
        current = verb
        for _ in range(3):
            current = current.head
            if current is verb:
                break
            subjects = [
                child
                for child in current.children
                if child.dep_ in {"nsubj", "nsubjpass"}
            ]
            if subjects:
                return subjects
        return []

    @staticmethod
    def _dedupe(candidates: list[RelationCandidate]) -> list[RelationCandidate]:
        unique: list[RelationCandidate] = []
        seen: set[tuple[str, str, str, str]] = set()
        for candidate in candidates:
            key = (
                candidate.subject,
                candidate.relationship,
                candidate.object,
                candidate.source_sentence,
            )
            if key in seen:
                continue
            seen.add(key)
            unique.append(candidate)
        return unique

    def _recover_dependency_conjuncts(self, sentence) -> list[RelationCandidate]:
        recovered: list[RelationCandidate] = []
        for verb in sentence:
            if verb.pos_ != "VERB" or verb.lemma_.lower() not in DEPENDENCY_LEMMAS:
                continue
            subjects = self._subject_mentions(verb)
            if not subjects:
                continue
            for pobj in self._prep_objects(verb, {"on", "upon", "from", "to"}):
                for conjunct in pobj.conjuncts:
                    recovered.extend(
                        self._emit(
                            sentence=sentence,
                            subjects=subjects,
                            objects=[self._mention(conjunct)],
                            relationship="DEPENDS_ON",
                            pattern_id="dependency_coordinated_prep",
                            voice="active",
                            extraction_confidence=0.94,
                        )
                    )
        return recovered

    def _recover_inherited_subject_production(self, sentence) -> list[RelationCandidate]:
        recovered: list[RelationCandidate] = []
        for verb in sentence:
            if verb.pos_ != "VERB" or verb.lemma_.lower() not in PRODUCTION_LEMMAS:
                continue
            if self._subject_mentions(verb):
                continue
            subjects = self._subject_from_ancestor(verb)
            if not subjects:
                continue
            objects = []
            for direct_object in self._direct_objects(verb):
                object_text = self._span_text(direct_object)
                if object_text:
                    objects.append((object_text, "Product"))
                for conjunct in direct_object.conjuncts:
                    conjunct_text = self._span_text(conjunct)
                    if conjunct_text:
                        objects.append((conjunct_text, "Product"))
            if objects:
                recovered.extend(
                    self._emit(
                        sentence=sentence,
                        subjects=subjects,
                        objects=objects,
                        relationship="PRODUCES",
                        pattern_id="production_inherited_subject",
                        voice="active",
                        extraction_confidence=0.92,
                    )
                )
        return recovered

    def _recover_nominal_production(self, sentence) -> list[RelationCandidate]:
        recovered: list[RelationCandidate] = []
        for noun in sentence:
            if noun.pos_ != "NOUN" or noun.lemma_.lower() not in _NOMINAL_PRODUCTION_LEMMAS:
                continue
            filing_ref = self._filing_reference_in_subtree(noun)
            if filing_ref is None:
                for ancestor in noun.ancestors:
                    filing_ref = self._filing_reference_in_subtree(ancestor)
                    if filing_ref is not None:
                        break
            if filing_ref is None:
                continue
            for pobj in self._prep_objects(noun, {"of"}):
                object_text = self._span_text(pobj)
                if not object_text:
                    continue
                recovered.append(
                    self._emit_explicit(
                        sentence=sentence,
                        subject_text=filing_ref.text,
                        subject_type=None,
                        object_text=object_text,
                        object_type="Product",
                        relationship="PRODUCES",
                        pattern_id="production_nominal_of",
                        extraction_confidence=0.91,
                        voice="active",
                    )
                )
        return recovered

    def _recover_passive_products(self, sentence) -> list[RelationCandidate]:
        recovered: list[RelationCandidate] = []
        for verb in sentence:
            if verb.pos_ != "VERB" or verb.lemma_.lower() not in PRODUCTION_LEMMAS:
                continue
            subjects = self._subject_mentions(verb)
            if not subjects or not any(subject.dep_ == "nsubjpass" for subject in subjects):
                continue
            agents = self._object_mentions(self._prep_objects(verb, {"by"}))
            for agent_text, agent_type in agents:
                is_filing_agent = self._is_filing_reference(agent_text)
                if not is_filing_agent and agent_type != "Company":
                    continue
                for subject in subjects:
                    object_text = self._span_text(subject)
                    if not object_text:
                        continue
                    recovered.append(
                        self._emit_explicit(
                            sentence=sentence,
                            subject_text=agent_text,
                            subject_type=agent_type,
                            object_text=object_text,
                            object_type="Product",
                            relationship="PRODUCES",
                            pattern_id="production_passive_product_fallback",
                            extraction_confidence=0.93,
                        )
                    )
        return recovered

    def _recover_owned_facility_via_interest(self, sentence) -> list[RelationCandidate]:
        recovered: list[RelationCandidate] = []
        for verb in sentence:
            if verb.pos_ != "VERB" or verb.lemma_.lower() != "own":
                continue
            subjects = self._subject_mentions(verb)
            if not subjects or any(subject.dep_ == "nsubjpass" for subject in subjects):
                continue
            direct_objects = self._direct_objects(verb)
            if not any(obj.lemma_.lower() in {"interest", "stake"} for obj in direct_objects):
                continue
            for prep_object in self._prep_objects(verb, {"in"}):
                head = prep_object.lemma_.lower()
                text = self._span_text(prep_object)
                if head not in _FACILITY_HEADS and not any(
                    term in text.lower() for term in _FACILITY_HEADS
                ):
                    continue
                recovered.extend(
                    self._emit(
                        sentence=sentence,
                        subjects=subjects,
                        objects=[(text, "Facility")],
                        relationship="OWNS",
                        pattern_id="facility_own_interest_in",
                        voice="active",
                        extraction_confidence=0.94,
                    )
                )
        return recovered

    def extract(self, text: str) -> list[RelationCandidate]:
        doc = self.nlp(text)
        # Base extractor parses text internally. Keeping the base implementation
        # unchanged protects its validated precision while these additions are
        # independently regression-tested.
        candidates = list(super().extract(text))
        for sentence in doc.sents:
            candidates.extend(self._recover_dependency_conjuncts(sentence))
            candidates.extend(self._recover_inherited_subject_production(sentence))
            candidates.extend(self._recover_nominal_production(sentence))
            candidates.extend(self._recover_passive_products(sentence))
            candidates.extend(self._recover_owned_facility_via_interest(sentence))
        return self._dedupe(candidates)
