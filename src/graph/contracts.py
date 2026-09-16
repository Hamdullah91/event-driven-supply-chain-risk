from __future__ import annotations

from typing import Any


CANONICAL_ID_PROPERTIES: dict[str, str] = {
    "Company": "company_id",
    "Facility": "facility_id",
    "Product": "product_id",
    "Material": "material_id",
    "Technology": "technology_id",
    "Industry": "industry_id",
    "Location": "location_id",
    "Country": "country_id",
    "Event": "event_id",
}

GEOGRAPHIC_COORDINATE_PROPERTIES = ("latitude", "longitude")


def canonical_graph_id(label: str, properties: dict[str, Any], *, element_id: str) -> str:
    """Return a stable graph id when the canonical identity property is populated."""
    identity_property = CANONICAL_ID_PROPERTIES.get(label)
    identity = properties.get(identity_property) if identity_property else None
    if identity is not None and str(identity).strip():
        return f"{label.lower()}:{identity}"
    return f"{label.lower()}:{element_id}"


def validate_coordinates(latitude: float | None, longitude: float | None) -> None:
    """Require coordinates to be supplied as a valid pair when present."""
    if latitude is None and longitude is None:
        return
    if latitude is None or longitude is None:
        raise ValueError("latitude and longitude must be provided together")
    if not -90.0 <= latitude <= 90.0:
        raise ValueError("latitude must be between -90 and 90")
    if not -180.0 <= longitude <= 180.0:
        raise ValueError("longitude must be between -180 and 180")
