from src.graph.ingestion.resolution import resolve_graph_candidates
from src.nlp.triplet_extractor import GraphCandidate


def _candidate(
    predicate: str,
    object_name: str,
    *,
    object_type: str | None = None,
) -> GraphCandidate:
    return GraphCandidate(
        subject="we",
        predicate=predicate,
        object=object_name,
        source_sentence="test sentence",
        object_type=object_type,
    )


def test_known_company_use_becomes_dependency() -> None:
    result = resolve_graph_candidates(
        [_candidate("USES", "TSMC", object_type="Company")],
        filing_company="Advanced Micro Devices, Inc.",
    )

    assert len(result) == 1
    assert result[0].subject == "Advanced Micro Devices"
    assert result[0].subject_type == "Company"
    assert result[0].relationship == "DEPENDS_ON"
    assert result[0].object == "Taiwan Semiconductor Manufacturing Company"
    assert result[0].object_type == "Company"


def test_business_unit_rolls_up_to_parent_company() -> None:
    result = resolve_graph_candidates(
        [_candidate("SUPPLIES", "Pratt & Whitney", object_type="Company")],
        filing_company="Boeing",
    )

    assert len(result) == 1
    assert result[0].object == "RTX Corporation"
    assert result[0].object_type == "Company"


def test_verified_external_company_is_preserved() -> None:
    result = resolve_graph_candidates(
        [_candidate("DEPENDS_ON", "Ford Otosan", object_type="Company")],
        filing_company="Ford Motor Company",
    )

    assert len(result) == 1
    assert result[0].subject == "Ford"
    assert result[0].relationship == "DEPENDS_ON"
    assert result[0].object == "Ford Otosan"
    assert result[0].object_type == "Company"


def test_untyped_material_is_inferred_conservatively() -> None:
    result = resolve_graph_candidates(
        [_candidate("USES", "silicon")],
        filing_company="NVIDIA Corporation",
    )

    assert len(result) == 1
    assert result[0].relationship == "USES"
    assert result[0].object == "silicon"
    assert result[0].object_type == "Material"


def test_untyped_technology_is_inferred_conservatively() -> None:
    result = resolve_graph_candidates(
        [_candidate("USES", "AI/ML")],
        filing_company="General Dynamics Corporation",
    )

    assert len(result) == 1
    assert result[0].relationship == "USES"
    assert result[0].object_type == "Technology"


def test_specific_facility_phrase_is_inferred() -> None:
    result = resolve_graph_candidates(
        [_candidate("OPERATES", "Penang manufacturing facility")],
        filing_company="Analog Devices, Inc.",
    )

    assert len(result) == 1
    assert result[0].relationship == "OPERATES"
    assert result[0].object_type == "Facility"


def test_spacy_product_type_is_preserved() -> None:
    result = resolve_graph_candidates(
        [
            _candidate(
                "PRODUCES",
                "MI300X accelerator",
                object_type="Product",
            )
        ],
        filing_company="Advanced Micro Devices, Inc.",
    )

    assert len(result) == 1
    assert result[0].relationship == "PRODUCES"
    assert result[0].object_type == "Product"


def test_generic_object_is_not_promoted_to_graph_node() -> None:
    result = resolve_graph_candidates(
        [_candidate("PRODUCES", "products")],
        filing_company="Applied Materials, Inc.",
    )

    assert result == []


def test_unknown_company_is_not_invented() -> None:
    result = resolve_graph_candidates(
        [
            _candidate(
                "SUPPLIES",
                "Completely Unknown Supplier LLC",
                object_type="Company",
            )
        ],
        filing_company="NVIDIA Corporation",
    )

    assert result == []


def test_ai_mislabeled_as_location_is_corrected_for_uses() -> None:
    result = resolve_graph_candidates(
        [_candidate("USES", "AI", object_type="Location")],
        filing_company="Tesla, Inc.",
    )

    assert len(result) == 1
    assert result[0].relationship == "USES"
    assert result[0].object == "AI"
    assert result[0].object_type == "Technology"


def test_location_is_rejected_for_supplies() -> None:
    result = resolve_graph_candidates(
        [_candidate("SUPPLIES", "AI", object_type="Location")],
        filing_company="NVIDIA Corporation",
    )

    assert result == []


def test_location_is_rejected_for_owns() -> None:
    result = resolve_graph_candidates(
        [_candidate("OWNS", "U.S.", object_type="Location")],
        filing_company="Lucid Group, Inc.",
    )

    assert result == []
