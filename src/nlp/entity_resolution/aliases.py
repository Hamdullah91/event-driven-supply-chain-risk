from __future__ import annotations

import json
from pathlib import Path

from .normalizer import normalize_entity_name


COMPANY_ALIASES: dict[str, str] = {
    "tsmc": "tsmc",
    "taiwan semiconductor manufacturing company": "tsmc",
    "taiwan semiconductor manufacturing company limited": "tsmc",
    "taiwan semiconductor manufacturing co": "tsmc",
    "taiwan semiconductor manufacturing co ltd": "tsmc",

    "nvidia": "nvidia",
    "nvidia corporation": "nvidia",
    "nvidia corp": "nvidia",

    "amd": "amd",
    "advanced micro devices": "amd",
    "advanced micro devices inc": "amd",

    "intel": "intel",
    "intel corporation": "intel",
    "intel corp": "intel",

    "qualcomm": "qualcomm",
    "qualcomm incorporated": "qualcomm",
    "qualcomm inc": "qualcomm",

    "broadcom": "broadcom",
    "broadcom inc": "broadcom",

    "micron": "micron",
    "micron technology": "micron",
    "micron technology inc": "micron",

    "texas instruments": "texas_instruments",
    "texas instruments incorporated": "texas_instruments",
    "texas instruments inc": "texas_instruments",

    "analog devices": "analog_devices",
    "analog devices inc": "analog_devices",

    "applied materials": "applied_materials",
    "applied materials inc": "applied_materials",

    "lam research": "lam_research",
    "lam research corporation": "lam_research",
    "lam research corp": "lam_research",

    "kla": "kla",
    "kla corporation": "kla",
    "kla corp": "kla",

    "tesla": "tesla",
    "tesla inc": "tesla",

    "rivian": "rivian",
    "rivian automotive": "rivian",
    "rivian automotive inc": "rivian",

    "lucid": "lucid",
    "lucid group": "lucid",
    "lucid group inc": "lucid",

    "gm": "general_motors",
    "general motors": "general_motors",
    "general motors company": "general_motors",

    "ford": "ford",
    "ford motor company": "ford",

    "albemarle": "albemarle",
    "albemarle corporation": "albemarle",
    "albemarle corp": "albemarle",

    "boeing": "boeing",
    "the boeing company": "boeing",
    "boeing co": "boeing",

    "lockheed martin": "lockheed_martin",
    "lockheed martin corporation": "lockheed_martin",
    "lockheed martin corp": "lockheed_martin",

    "rtx": "rtx",
    "rtx corporation": "rtx",

    "northrop grumman": "northrop_grumman",
    "northrop grumman corporation": "northrop_grumman",
    "northrop grumman corp": "northrop_grumman",

    "general dynamics": "general_dynamics",
    "general dynamics corporation": "general_dynamics",
    "general dynamics corp": "general_dynamics",

    "honeywell": "honeywell",
    "honeywell international": "honeywell",
    "honeywell international inc": "honeywell",

    "ge aerospace": "ge_aerospace",

    "l3harris": "l3harris",
    "l3harris technologies": "l3harris",
    "l3harris technologies inc": "l3harris",

    "teledyne": "teledyne",
    "teledyne technologies": "teledyne",
    "teledyne technologies incorporated": "teledyne",

    "transdigm": "transdigm",
    "transdigm group": "transdigm",
    "transdigm group incorporated": "transdigm",

    "samsung electronics": "samsung_electronics",
    "samsung electronics co ltd": "samsung_electronics",
    "samsung": "samsung_electronics",

    "sk hynix": "sk_hynix",
    "sk hynix inc": "sk_hynix",

    "asml": "asml",
    "asml holding": "asml",
    "asml holding nv": "asml",

    "globalfoundries": "globalfoundries",
    "globalfoundries inc": "globalfoundries",
    "gf": "globalfoundries",

    "united microelectronics corporation": "umc",
    "united microelectronics corp": "umc",
    "umc": "umc",
}


def _baseline_company_path() -> Path:
    return Path(__file__).resolve().parents[3] / "data" / "seed" / "companies.json"


def _extend_aliases_from_baseline() -> None:
    """Register every baseline display name and legal name as exact aliases."""
    path = _baseline_company_path()
    if not path.exists():
        return

    companies = json.loads(path.read_text(encoding="utf-8"))
    for company in companies:
        company_id = str(company["company_id"]).strip()
        if not company_id:
            continue

        for field in ("name", "legal_name"):
            value = str(company.get(field, "")).strip()
            if not value:
                continue
            COMPANY_ALIASES.setdefault(
                normalize_entity_name(value),
                company_id,
            )


_extend_aliases_from_baseline()
