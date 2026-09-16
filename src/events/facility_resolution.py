from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path


SEED_PATH = Path(__file__).resolve().parents[2] / "data" / "seed" / "facilities.json"


def _normalize(value: str) -> str:
    return " ".join(value.casefold().replace("-", " ").split())


@lru_cache(maxsize=1)
def _facilities() -> tuple[dict, ...]:
    return tuple(json.loads(SEED_PATH.read_text(encoding="utf-8")))


def resolve_facility_mentions(texts: list[str]) -> list[tuple[str, str]]:
    """Resolve explicit seeded facility names to (facility_id, match_method)."""
    haystack = _normalize("\n".join(text for text in texts if text))
    matches: list[tuple[str, str]] = []
    for facility in _facilities():
        name = _normalize(str(facility["name"]))
        if name and name in haystack:
            matches.append((str(facility["facility_id"]), "facility_name_exact"))
    return matches
