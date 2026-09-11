from src.nlp.entity_resolution.organizational_identity import (
    resolve_organizational_identity,
)


def test_raytheon_rolls_up_to_rtx():
    identity = resolve_organizational_identity("Raytheon")
    assert identity is not None
    assert identity.identity_type == "BUSINESS_UNIT"
    assert identity.parent_company_id == "rtx"
    assert identity.normalized_name == "RTX Corporation"


def test_pratt_and_whitney_rolls_up_to_rtx():
    identity = resolve_organizational_identity("Pratt & Whitney")
    assert identity is not None
    assert identity.parent_company_id == "rtx"


def test_qct_rolls_up_to_qualcomm():
    identity = resolve_organizational_identity("QCT")
    assert identity is not None
    assert identity.parent_company_id == "qualcomm"


def test_gdit_rolls_up_to_general_dynamics():
    identity = resolve_organizational_identity("GDIT")
    assert identity is not None
    assert identity.parent_company_id == "general_dynamics"


def test_ford_otosan_is_preserved_as_external_org():
    identity = resolve_organizational_identity("Ford Otosan")
    assert identity is not None
    assert identity.identity_type == "VERIFIED_EXTERNAL"
    assert identity.parent_company_id is None


def test_unknown_org_has_no_forced_identity():
    assert resolve_organizational_identity("Unknown Supplier LLC") is None
