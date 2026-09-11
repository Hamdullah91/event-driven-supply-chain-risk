from scripts.diagnose_sec_extraction_waterfall import (
    _classify_failure,
    _trigger_counts,
)


def test_trigger_counts_detects_source_from_language() -> None:
    total, families, _ = _trigger_counts(
        "We source semiconductor wafers from external foundries."
    )

    assert total >= 1
    assert families["DEPENDENCY"] >= 1


def test_trigger_counts_detects_manufactured_by_language() -> None:
    total, families, _ = _trigger_counts(
        "Our processors are manufactured by a third-party foundry."
    )

    assert total >= 1
    assert families["DEPENDENCY"] >= 1


def test_classifies_trigger_blind_extractor() -> None:
    status = _classify_failure(
        text_chars=1000,
        trigger_hits=12,
        raw_triplets=0,
        resolved_edges=0,
    )

    assert status == "TRIGGERS_PRESENT_BUT_NO_RAW_TRIPLETS"


def test_classifies_downstream_rejection() -> None:
    status = _classify_failure(
        text_chars=1000,
        trigger_hits=12,
        raw_triplets=8,
        resolved_edges=0,
    )

    assert status == "RAW_TRIPLETS_REJECTED_DOWNSTREAM"
