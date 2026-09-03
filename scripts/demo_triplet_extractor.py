import spacy

from src.nlp.triplet_extractor import TripletExtractor


nlp = spacy.load("en_core_web_sm")

extractor = TripletExtractor(nlp)

text = """
TSMC provides chips to NVIDIA.
Tesla uses lithium.
Intel produces processors.
Apple owns facilities.
"""

triplets = extractor.extract(text)

for triplet in triplets:
    print(
        f"{triplet.subject} "
        f"--[{triplet.predicate}]--> "
        f"{triplet.object}"
    )