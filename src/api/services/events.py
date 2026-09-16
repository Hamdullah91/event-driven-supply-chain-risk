from __future__ import annotations

from typing import Any

from src.events.read_repository import EventReadRepository


class EventReadService:
    """Application service for read-only Event operations."""

    def __init__(self, repository: EventReadRepository) -> None:
        self.repository = repository

    def list_events(self, *, limit: int, offset: int) -> dict[str, Any]:
        return {
            "events": self.repository.list_events(limit=limit, offset=offset),
            "count": self.repository.count_events(),
            "limit": limit,
            "offset": offset,
        }

    def get_event(self, event_id: str) -> dict[str, Any] | None:
        return self.repository.get_event(event_id)
