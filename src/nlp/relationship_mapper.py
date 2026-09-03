RELATIONSHIP_MAP = {
    "SUPPLY": "SUPPLIES",
    "PROVIDE": "SUPPLIES",
    "DELIVER": "SUPPLIES",

    "USE": "USES",
    "UTILIZE": "USES",

    "PRODUCE": "PRODUCES",
    "MANUFACTURE": "PRODUCES",

    "OPERATE": "OPERATES",
    "OWN": "OWNS",

    "DEPEND": "DEPENDS_ON",
    "RELY": "DEPENDS_ON",
}


def normalize_relationship(verb: str) -> str | None:
    """Map a verb lemma to an allowed knowledge-graph relationship."""
    return RELATIONSHIP_MAP.get(verb.upper())
