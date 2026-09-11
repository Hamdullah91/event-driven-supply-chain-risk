from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class OrganizationalIdentity:
    mention: str
    normalized_name: str
    parent_company_id: str | None
    identity_type: str
    confidence: float


# High-confidence business-unit rollups. These are only used for mentions that
# are organizational units/brands of a filing company and should not become
# separate top-level Company nodes.
BUSINESS_UNIT_ROLLUPS: dict[str, tuple[str, str]] = {
    "raytheon": ("RTX Corporation", "rtx"),
    "raytheon technologies": ("RTX Corporation", "rtx"),
    "pratt & whitney": ("RTX Corporation", "rtx"),
    "pratt and whitney": ("RTX Corporation", "rtx"),
    "collins aerospace": ("RTX Corporation", "rtx"),
    "qct": ("Qualcomm", "qualcomm"),
    "qualcomm cdma technologies": ("Qualcomm", "qualcomm"),
    "qgov": ("Qualcomm", "qualcomm"),
    "qualcomm government technologies": ("Qualcomm", "qualcomm"),
    "electric boat": ("General Dynamics", "general_dynamics"),
    "bath iron works": ("General Dynamics", "general_dynamics"),
    "gdit": ("General Dynamics", "general_dynamics"),
    "general dynamics information technology": ("General Dynamics", "general_dynamics"),
}

# Entities that may be related to a core company but are legally distinct and
# therefore must never be silently rolled up to the core company.
VERIFIED_EXTERNAL_ORGANIZATIONS = {
    "ford otosan",
}


def normalize_organizational_mention(value: str) -> str:
    return " ".join(value.lower().replace("’", "'").split())


def resolve_organizational_identity(value: str) -> OrganizationalIdentity | None:
    normalized = normalize_organizational_mention(value)

    rollup = BUSINESS_UNIT_ROLLUPS.get(normalized)
    if rollup is not None:
        parent_name, parent_company_id = rollup
        return OrganizationalIdentity(
            mention=value,
            normalized_name=parent_name,
            parent_company_id=parent_company_id,
            identity_type="BUSINESS_UNIT",
            confidence=0.99,
        )

    if normalized in VERIFIED_EXTERNAL_ORGANIZATIONS:
        return OrganizationalIdentity(
            mention=value,
            normalized_name=value,
            parent_company_id=None,
            identity_type="VERIFIED_EXTERNAL",
            confidence=0.95,
        )

    return None
