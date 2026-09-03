from dataclasses import dataclass
import token

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

    def extract(self, text: str) -> list[GraphCandidate]:
        doc = self.nlp(text)

        triplets = []

        for sentence in doc.sents:
            for token in sentence:

                if token.pos_ != "VERB":
                    continue

                predicate = normalize_relationship(token.lemma_)
                if predicate is None:
                    continue

                subjects = [
                    child
                    for child in token.children
                    if child.dep_ in {"nsubj", "nsubjpass"}
                ]

                # Direct objects, e.g. "Tesla uses lithium"
                direct_objects = [
                    child
                    for child in token.children
                    if child.dep_ in {
                        "dobj",
                        "obj",
                        "attr",
                        "dative",
                    }
                ]

                # Destination objects, e.g. "TSMC provides chips to NVIDIA"
                destination_objects = []

                for child in token.children:
                    if child.dep_ == "prep" and child.text.lower() in {"to", "for"}:
                        for pobj in child.children:
                            if pobj.dep_ == "pobj":
                                destination_objects.append(pobj)

                # For SUPPLIES, prefer the destination company/entity.
                # Otherwise use the normal direct object.
                if predicate == "SUPPLIES" and destination_objects:
                    objects = destination_objects
                else:
                    objects = direct_objects

                # Handle: "provides chips to NVIDIA"
                for child in token.children:
                    if child.dep_ == "prep" and child.text.lower() in {"to", "for"}:
                        for pobj in child.children:
                            if pobj.dep_ == "pobj":
                                objects.append(pobj)

                for subject in subjects:
                    for obj in objects:
                        triplets.append(
                            GraphCandidate(
                                subject=subject.text,
                                predicate=predicate,
                                object=obj.text,
                                source_sentence=sentence.text.strip(),
                                confidence=1.0,
                            )
                        )

        unique_triplets = []

        seen = set()

        for triplet in triplets:
            key = (
                triplet.subject,
                triplet.predicate,
                triplet.object,
            )

            if key not in seen:
                seen.add(key)
                unique_triplets.append(triplet)

        return unique_triplets