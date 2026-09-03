import spacy


nlp = spacy.load("en_core_web_sm")

text = """
NVIDIA relies on TSMC for semiconductor manufacturing
in Taiwan and uses advanced silicon wafers for GPU production.
"""

doc = nlp(text)

for ent in doc.ents:
    print(ent.text, "->", ent.label_)