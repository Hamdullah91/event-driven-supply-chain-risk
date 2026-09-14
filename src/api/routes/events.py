from fastapi import APIRouter

from src.api.schemas import EventRequest


router = APIRouter(prefix="/api/v1/events", tags=["events"])


@router.post("/validate", response_model=EventRequest)
def validate_event(event: EventRequest) -> EventRequest:
    """Validate an event payload without mutating the knowledge graph."""
    return event
