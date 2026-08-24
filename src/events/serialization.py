"""
Serialization utilities for supply chain events.
"""

import json
from dataclasses import asdict
from datetime import datetime
from typing import Any

from src.events.models import SupplyChainEvent


def event_to_dict(event: SupplyChainEvent) -> dict[str, Any]:
    """
    Convert a SupplyChainEvent into a JSON-compatible dictionary.
    """

    data = asdict(event)

    data["event_id"] = str(data["event_id"])
    data["event_type"] = data["event_type"].value
    data["severity"] = data["severity"].value

    data["timestamp"] = data["timestamp"].isoformat()
    data["created_at"] = data["created_at"].isoformat()

    return data


def event_to_json(event: SupplyChainEvent) -> str:
    """
    Serialize a SupplyChainEvent into JSON.
    """

    return json.dumps(event_to_dict(event), indent=2)