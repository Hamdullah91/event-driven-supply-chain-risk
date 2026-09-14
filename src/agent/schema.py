from __future__ import annotations

from collections import defaultdict

from src.nlp.validation.relationship_rules import VALID_RELATIONSHIPS


NODE_PROPERTIES: dict[str, tuple[str, ...]] = {
    "Company": ("company_id", "name", "legal_name", "entity_type"),
    "Supplier": ("supplier_id", "name"),
    "Facility": ("facility_id", "name"),
    "Product": ("product_id", "name"),
    "Material": ("material_id", "name"),
    "Location": ("location_id", "name"),
    "Country": ("country_id", "name"),
    "Event": (
        "event_id",
        "event_type",
        "timestamp",
        "severity",
        "source",
        "confidence",
        "description",
    ),
    "Industry": ("industry_id", "name"),
    "Technology": ("technology_id", "name"),
}


def relationship_dictionary() -> tuple[tuple[str, str, str], ...]:
    return tuple(sorted(VALID_RELATIONSHIPS))


def allowed_labels() -> tuple[str, ...]:
    labels = set(NODE_PROPERTIES)
    for source, _, target in VALID_RELATIONSHIPS:
        labels.add(source)
        labels.add(target)
    return tuple(sorted(labels))


def allowed_relationship_types() -> tuple[str, ...]:
    return tuple(sorted({relationship for _, relationship, _ in VALID_RELATIONSHIPS}))


def build_graph_schema_context() -> str:
    """Build prompt context from the project's maintained graph relationship rules."""

    lines = ["Allowed node labels and known properties:"]
    for label in allowed_labels():
        properties = ", ".join(NODE_PROPERTIES.get(label, ())) or "unspecified"
        lines.append(f"- {label}: {properties}")

    lines.append("")
    lines.append("Allowed directed relationships:")
    grouped: dict[str, list[str]] = defaultdict(list)
    for source, relationship, target in relationship_dictionary():
        grouped[source].append(f"(:{source})-[:{relationship}]->(:{target})")

    for source in sorted(grouped):
        for pattern in grouped[source]:
            lines.append(f"- {pattern}")

    return "\n".join(lines)
