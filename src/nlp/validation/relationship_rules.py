from __future__ import annotations

from typing import Final


VALID_RELATIONSHIPS: Final[frozenset[tuple[str, str, str]]] = frozenset(
    {
        ("Company", "SUPPLIES", "Company"),
        ("Company", "DEPENDS_ON", "Company"),

        ("Company", "OPERATES", "Facility"),
        ("Company", "OWNS", "Facility"),

        ("Company", "USES", "Material"),
        ("Company", "USES", "Technology"),

        ("Company", "PRODUCES", "Product"),
        ("Company", "PRODUCES", "Material"),

        ("Company", "OPERATES_IN", "Industry"),

        ("Facility", "LOCATED_IN", "Location"),
        ("Location", "LOCATED_IN", "Country"),

        ("Event", "AFFECTS", "Company"),
        ("Event", "AFFECTS", "Facility"),
        ("Event", "OCCURS_AT", "Facility"),
    }
)