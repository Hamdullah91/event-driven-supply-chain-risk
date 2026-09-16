from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status

from src.api.dependencies import get_event_service, get_risk_service
from src.api.schemas import (
    EventBlastRadiusResponse,
    EventDetail,
    EventListResponse,
    EventRequest,
)
from src.api.services.events import EventReadService
from src.api.services.risk import RiskAnalyticsService


router = APIRouter(prefix="/api/v1/events", tags=["events"])


@router.get("", response_model=EventListResponse)
def list_events(
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    service: EventReadService = Depends(get_event_service),
) -> EventListResponse:
    """Return persisted events ordered from newest to oldest."""
    return EventListResponse(**service.list_events(limit=limit, offset=offset))


@router.get("/{event_id}/blast-radius", response_model=EventBlastRadiusResponse)
def get_event_blast_radius(
    event_id: str,
    max_hops: Annotated[int, Query(ge=1, le=3)] = 3,
    service: RiskAnalyticsService = Depends(get_risk_service),
) -> EventBlastRadiusResponse:
    """Return direct and downstream company risk caused by one event."""
    if not service.event_exists(event_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Event '{event_id}' was not found.",
        )
    return EventBlastRadiusResponse(
        **service.get_event_blast_radius(event_id, max_hops=max_hops)
    )


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
