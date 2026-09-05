from __future__ import annotations

from dataclasses import dataclass

from src.nlp.relationship_mapper import normalize_relationship


@dataclass(frozen=True)
class Triplet:
    subject: str
    predicate: str
    object: str
    source_sentence: str


@dataclass(frozen=True)
class GraphCandidate:
    subject: str
    predicate: str
    object: str
    source_sentence: str
    confidence: float = 1.0


class TripletExtractor:
    def __init__(self, nlp):
        self.nlp = nlp

    @staticmethod
    def _full_entity_text(token) -> str:
        """
        If the token belongs to a spaCy named entity,
        return the complete entity text.

        Example:
            token='Company'
            -> 'Taiwan Semiconductor Manufacturing Company Limited'
        """
        for ent in token.doc.ents:
            if ent.start <= token.i < ent.end:
                return ent.text

        return token.text

    @staticmethod
    def _organization_entities_in_subtree(token) -> list[str]:
        """
        Find organization entities contained inside the dependency
        subtree rooted at the supplied token.

        Example:
            foundries
              └── such as TSMC and Samsung

        returns:
            [
                'Taiwan Semiconductor Manufacturing Company Limited',
                'Samsung Electronics Co., Ltd.'
            ]
        """
        subtree_indexes = {
            subtree_token.i
            for subtree_token in token.subtree
        }

        organizations: list[str] = []

        for ent in token.doc.ents:
            if ent.label_ != "ORG":
                continue

            entity_indexes = set(
                range(ent.start, ent.end)
            )

            if subtree_indexes.intersection(entity_indexes):
                organizations.append(ent.text)

        return organizations

    def extract(self, text: str) -> list[GraphCandidate]:
        doc = self.nlp(text)

        triplets: list[GraphCandidate] = []

        for sentence in doc.sents:
            for verb in sentence:

                if verb.pos_ != "VERB":
                    continue

                predicate = normalize_relationship(
                    verb.lemma_
                )

                if predicate is None:
                    continue

                subjects = [
                    child
                    for child in verb.children
                    if child.dep_ in {
                        "nsubj",
                        "nsubjpass",
                    }
                ]

                direct_objects = [
                    child
                    for child in verb.children
                    if child.dep_ in {
                        "dobj",
                        "obj",
                        "attr",
                        "dative",
                    }
                ]

                destination_objects = []

                for child in verb.children:
                    if (
                        child.dep_ == "prep"
                        and child.text.lower()
                        in {"to", "for"}
                    ):
                        for pobj in child.children:
                            if pobj.dep_ == "pobj":
                                destination_objects.append(
                                    pobj
                                )

                if (
                    predicate == "SUPPLIES"
                    and destination_objects
                ):
                    objects = destination_objects
                else:
                    objects = direct_objects

                # Include destination objects for patterns like:
                # "provides chips to NVIDIA"
                for destination in destination_objects:
                    if destination not in objects:
                        objects.append(destination)

                for subject in subjects:

                    subject_text = self._full_entity_text(
                        subject
                    )

                    for obj in objects:

                        # Prefer named organizations contained
                        # within generic object phrases.
                        organization_objects = (
                            self._organization_entities_in_subtree(
                                obj
                            )
                        )

                        if organization_objects:
                            object_names = organization_objects
                        else:
                            object_names = [
                                self._full_entity_text(obj)
                            ]

                        for object_name in object_names:
                            triplets.append(
                                GraphCandidate(
                                    subject=subject_text,
                                    predicate=predicate,
                                    object=object_name,
                                    source_sentence=(
                                        sentence.text.strip()
                                    ),
                                    confidence=1.0,
                                )
                            )

        unique_triplets: list[GraphCandidate] = []

        seen = set()

        for triplet in triplets:
            key = (
                triplet.subject,
                triplet.predicate,
                triplet.object,
            )

            if key in seen:
                continue

            seen.add(key)
            unique_triplets.append(triplet)

        return unique_triplets