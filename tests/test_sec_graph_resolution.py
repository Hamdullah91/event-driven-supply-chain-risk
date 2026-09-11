from src.graph.ingestion.resolution import resolve_graph_candidates
from src.nlp.triplet_extractor import GraphCandidate


def test_sec_we_uses_named_suppliers_becomes_dependencies():
    candidates = [
        GraphCandidate(
            subject="We",
            predicate="USES",
            object="GLOBALFOUNDRIES Inc.",
            source_sentence="We utilize GLOBALFOUNDRIES Inc. for wafer production.",
        ),
        GraphCandidate(
            subject="we",
            predicate="USES",
            object="United Microelectronics Corporation",
            source_sentence="We utilize UMC for production.",
        ),
        GraphCandidate(
            subject="we",
            predicate="USES",
            object="Samsung Electronics Co., Ltd.",
            source_sentence="We utilize Samsung Electronics for production.",
        ),
    ]

    resolved = resolve_graph_candidates(
        candidates,
        filing_company="Advanced Micro Devices, Inc.",
    )

    assert {
        (item.subject, item.relationship, item.object)
        for item in resolved
    } == {
        (
            "Advanced Micro Devices",
            "DEPENDS_ON",
            "GlobalFoundries",
        ),
        (
            "Advanced Micro Devices",
            "DEPENDS_ON",
            "United Microelectronics Corporation",
        ),
        (
            "Advanced Micro Devices",
            "DEPENDS_ON",
            "Samsung Electronics",
        ),
    }


def test_the_company_reference_uses_filing_company():
    candidates = [
        GraphCandidate(
            subject="Company",
            predicate="USES",
            object="TSMC",
            source_sentence="The Company utilizes TSMC.",
        )
    ]

    resolved = resolve_graph_candidates(
        candidates,
        filing_company="NVIDIA Corporation",
    )

    assert len(resolved) == 1
    assert resolved[0].subject == "NVIDIA Corporation"
    assert resolved[0].relationship == "DEPENDS_ON"
    assert resolved[0].object == "Taiwan Semiconductor Manufacturing Company"


def test_unresolved_generic_supplier_is_not_invented():
    candidates = [
        GraphCandidate(
            subject="Company",
            predicate="DEPENDS_ON",
            object="single-source partners",
            source_sentence="The Company relies on single-source partners.",
        )
    ]

    resolved = resolve_graph_candidates(
        candidates,
        filing_company="Apple Inc.",
    )

    assert resolved == []
