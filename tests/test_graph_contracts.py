import pytest

from src.graph.contracts import CANONICAL_ID_PROPERTIES, canonical_graph_id, validate_coordinates


def test_all_frontend_graph_labels_have_canonical_identity_properties():
    assert CANONICAL_ID_PROPERTIES == {
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


def test_canonical_graph_id_prefers_domain_identity():
    assert canonical_graph_id("Company", {"company_id": "tsmc"}, element_id="42") == "company:tsmc"


def test_canonical_graph_id_has_explicit_neo4j_fallback():
    assert canonical_graph_id("Facility", {"name": "Unknown Fab"}, element_id="42") == "facility:42"


def test_coordinate_contract_accepts_absent_or_valid_pairs():
    validate_coordinates(None, None)
    validate_coordinates(23.0, 121.0)
    validate_coordinates(-90.0, -180.0)
    validate_coordinates(90.0, 180.0)


@pytest.mark.parametrize("latitude,longitude", [(23.0, None), (None, 121.0), (91.0, 0.0), (-91.0, 0.0), (0.0, 181.0), (0.0, -181.0)])
def test_coordinate_contract_rejects_partial_or_invalid_pairs(latitude, longitude):
    with pytest.raises(ValueError):
        validate_coordinates(latitude, longitude)
