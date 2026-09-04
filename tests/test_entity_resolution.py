from src.nlp.entity_resolution.normalizer import normalize_entity_name
from src.nlp.entity_resolution.resolver import resolve_company


def test_normalize_entity_name():
    result = normalize_entity_name(
        "Taiwan Semiconductor Manufacturing Co., Ltd."
    )

    assert result == "taiwan semiconductor manufacturing co ltd"


def test_resolve_tsmc_alias():
    result = resolve_company("TSMC")

    assert result.canonical_id == "company_tsmc"
    assert result.canonical_name == "Taiwan Semiconductor Manufacturing Company"
    assert result.confidence == 1.0
    assert result.resolution_method == "alias_exact"


def test_resolve_tsmc_full_name():
    result = resolve_company(
        "Taiwan Semiconductor Manufacturing Company"
    )

    assert result.canonical_id == "company_tsmc"


def test_resolve_nvidia():
    result = resolve_company("NVIDIA Corp.")

    assert result.canonical_id == "company_nvidia"
    assert result.canonical_name == "NVIDIA Corporation"


def test_unresolved_company():
    result = resolve_company("Unknown Supplier XYZ")

    assert result.canonical_id is None
    assert result.canonical_name is None
    assert result.confidence == 0.0
    assert result.resolution_method == "unresolved"

def test_fuzzy_resolve_nvidia_typo():
    result = resolve_company("Nvidia Corporaton")

    assert result.canonical_id == "company_nvidia"
    assert result.canonical_name == "NVIDIA Corporation"
    assert result.resolution_method == "alias_fuzzy"
    assert result.confidence >= 0.85


def test_fuzzy_resolve_general_motors():
    result = resolve_company("General Motor Company")

    assert result.canonical_id == "company_general_motors"
    assert result.resolution_method == "alias_fuzzy"
    assert result.confidence >= 0.85


def test_bad_match_stays_unresolved():
    result = resolve_company("Completely Random Supplier")

    assert result.canonical_id is None
    assert result.canonical_name is None
    assert result.resolution_method == "unresolved"

def test_resolve_multiple_companies():
    from src.nlp.entity_resolution.resolver import resolve_companies

    results = resolve_companies([
        "TSMC",
        "NVIDIA Corp.",
        "Intel Corporation",
        "Unknown Supplier XYZ",
    ])

    assert len(results) == 4

    assert results[0].canonical_id == "company_tsmc"
    assert results[1].canonical_id == "company_nvidia"
    assert results[2].canonical_id == "company_intel"

    assert results[3].canonical_id is None
    assert results[3].resolution_method == "unresolved"

from src.nlp.entity_resolution.integration import (
    resolve_extracted_companies,
)


def test_resolve_extracted_companies_removes_duplicates():
    results = resolve_extracted_companies([
        "TSMC",
        "NVIDIA Corp.",
        "TSMC",
    ])

    assert len(results) == 2
    assert results[0].canonical_id == "company_tsmc"
    assert results[1].canonical_id == "company_nvidia"

def test_resolution_stats():
    from src.nlp.entity_resolution.integration import (
        get_resolution_stats,
        resolve_extracted_companies,
    )

    results = resolve_extracted_companies([
        "TSMC",
        "NVIDIA",
        "Unknown Supplier XYZ",
    ])

    stats = get_resolution_stats(results)

    assert stats["total"] == 3
    assert stats["resolved"] == 2
    assert stats["unresolved"] == 1
    assert stats["resolution_rate"] == 2 / 3

def test_resolve_amd():
    result = resolve_company("AMD")

    assert result.canonical_id == "company_amd"
    assert result.canonical_name == "Advanced Micro Devices"
    assert result.resolution_method == "alias_exact"


def test_resolve_rtx():
    result = resolve_company("RTX")

    assert result.canonical_id == "company_rtx"
    assert result.canonical_name == "RTX Corporation"


def test_resolve_samsung():
    result = resolve_company("Samsung Electronics")

    assert result.canonical_id == "company_samsung_electronics"


def test_resolve_sk_hynix():
    result = resolve_company("SK Hynix")

    assert result.canonical_id == "company_sk_hynix"


def test_resolve_texas_instruments():
    result = resolve_company("Texas Instruments")

    assert result.canonical_id == "company_texas_instruments"