from __future__ import annotations

import pytest

from src.graph.ingestion.repository import GraphIngestionRepository


def test_company_subject_merge_uses_company_id() -> None:
    clause, params = GraphIngestionRepository._node_merge(
        role="subject",
        node_type="Company",
        name="Advanced Micro Devices",
    )

    assert "MERGE (subject:Company {company_id: $subject_id})" in clause
    assert "{name: $subject_name}" not in clause
    assert params["subject_id"] == "amd"
    assert params["subject_identity_state"] == "CANONICAL"


def test_company_object_merge_uses_company_id() -> None:
    clause, params = GraphIngestionRepository._node_merge(
        role="object",
        node_type="Company",
        name="Taiwan Semiconductor Manufacturing Company",
    )

    assert "MERGE (object:Company {company_id: $object_id})" in clause
    assert "{name: $object_name}" not in clause
    assert params["object_id"] == "tsmc"
    assert params["object_identity_state"] == "CANONICAL"


def test_verified_external_company_endpoint_has_stable_external_id() -> None:
    clause, params = GraphIngestionRepository._node_merge(
        role="object",
        node_type="Company",
        name="Ford Otosan",
    )

    assert "MERGE (object:Company {company_id: $object_id})" in clause
    assert params["object_id"] == "external:ford_otosan"
    assert params["object_identity_state"] == "VERIFIED_EXTERNAL"


def test_non_company_endpoint_still_merges_by_name() -> None:
    clause, params = GraphIngestionRepository._node_merge(
        role="object",
        node_type="Product",
        name="vehicles",
    )

    assert clause == "MERGE (object:Product {name: $object_name})"
    assert params == {"object_name": "vehicles"}


def test_unresolved_company_endpoint_is_rejected() -> None:
    with pytest.raises(ValueError, match="Cannot persist unresolved Company entity"):
        GraphIngestionRepository._node_merge(
            role="subject",
            node_type="Company",
            name="Completely Unknown Supplier LLC",
        )
