from __future__ import annotations

import json
from pathlib import Path


CANONICAL_COMPANIES: dict[str, dict[str, str]] = {
    "tsmc": {"name": "Taiwan Semiconductor Manufacturing Company", "entity_type": "Company"},
    "nvidia": {"name": "NVIDIA Corporation", "entity_type": "Company"},
    "amd": {"name": "Advanced Micro Devices", "entity_type": "Company"},
    "intel": {"name": "Intel Corporation", "entity_type": "Company"},
    "qualcomm": {"name": "Qualcomm", "entity_type": "Company"},
    "broadcom": {"name": "Broadcom", "entity_type": "Company"},
    "micron": {"name": "Micron Technology", "entity_type": "Company"},
    "texas_instruments": {"name": "Texas Instruments", "entity_type": "Company"},
    "analog_devices": {"name": "Analog Devices", "entity_type": "Company"},
    "applied_materials": {"name": "Applied Materials", "entity_type": "Company"},
    "lam_research": {"name": "Lam Research", "entity_type": "Company"},
    "kla": {"name": "KLA", "entity_type": "Company"},
    "tesla": {"name": "Tesla", "entity_type": "Company"},
    "rivian": {"name": "Rivian", "entity_type": "Company"},
    "lucid": {"name": "Lucid", "entity_type": "Company"},
    "general_motors": {"name": "General Motors", "entity_type": "Company"},
    "ford": {"name": "Ford", "entity_type": "Company"},
    "albemarle": {"name": "Albemarle", "entity_type": "Company"},
    "boeing": {"name": "Boeing", "entity_type": "Company"},
    "lockheed_martin": {"name": "Lockheed Martin", "entity_type": "Company"},
    "rtx": {"name": "RTX Corporation", "entity_type": "Company"},
    "northrop_grumman": {"name": "Northrop Grumman", "entity_type": "Company"},
    "general_dynamics": {"name": "General Dynamics", "entity_type": "Company"},
    "honeywell": {"name": "Honeywell", "entity_type": "Company"},
    "ge_aerospace": {"name": "GE Aerospace", "entity_type": "Company"},
    "l3harris": {"name": "L3Harris Technologies", "entity_type": "Company"},
    "teledyne": {"name": "Teledyne Technologies", "entity_type": "Company"},
    "transdigm": {"name": "TransDigm", "entity_type": "Company"},
    "samsung_electronics": {"name": "Samsung Electronics", "entity_type": "Company"},
    "sk_hynix": {"name": "SK Hynix", "entity_type": "Company"},
    "asml": {"name": "ASML Holding N.V.", "entity_type": "Company"},
    "globalfoundries": {"name": "GlobalFoundries", "entity_type": "Company"},
    "umc": {"name": "United Microelectronics Corporation", "entity_type": "Company"},
}


def _baseline_company_path() -> Path:
    return Path(__file__).resolve().parents[3] / "data" / "seed" / "companies.json"


def _extend_from_baseline() -> None:
    """Ensure every seeded baseline company has a canonical company ID.

    Existing hand-curated canonical labels are preserved because they are used by
    evaluated SEC relation outputs. Missing baseline companies inherit their
    stable display name from the seed registry.
    """
    path = _baseline_company_path()
    if not path.exists():
        return

    companies = json.loads(path.read_text(encoding="utf-8"))
    for company in companies:
        company_id = str(company["company_id"]).strip()
        name = str(company["name"]).strip()
        if not company_id or not name:
            continue
        CANONICAL_COMPANIES.setdefault(
            company_id,
            {"name": name, "entity_type": "Company"},
        )


_extend_from_baseline()
