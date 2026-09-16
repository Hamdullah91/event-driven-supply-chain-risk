from fastapi import APIRouter, Depends, HTTPException, Query, status

from src.api.dependencies import get_event_service
from src.api.schemas import EventDetail, EventListResponse, EventRequest
from src.api.services.events import EventReadService


router = APIRouter(prefix="/api/v1/events", tags=["events"])


@router.get("", response_model=EventListResponse)
def list_events(
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    service: EventReadService = Depends(get_event_service),
) -> EventListResponse:
    """Return persisted events ordered from newest to oldest."""
    return EventListResponse(**service.list_events(limit=limit, offset=offset))


@router.get("/{event_id}", response_model=EventDetail)
def get_event(
    event_id: str,
    service: EventReadService = Depends(get_event_service),
) -> EventDetail:
    """Return one persisted event by its stable event ID."""
    event = service.get_event(event_id)
    if event is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found",
        )
    return EventDetail(**event)


@router.post("/validate", response_model=EventRequest)
def validate_event(event: EventRequest) -> EventRequest:
    """Validate an event payload without mutating the knowledge graph."""
    return event
