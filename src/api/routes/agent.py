from fastapi import APIRouter, Depends, HTTPException, status

from src.api.dependencies import get_agent_service
from src.api.schemas import AgentQueryRequest, AgentQueryResponse, EvidenceProvenance
from src.api.services.agent import AgentQueryService
from src.provenance import EvidenceAvailability


router = APIRouter(prefix="/api/v1/agent", tags=["agent"])


@router.post("/query", response_model=AgentQueryResponse)
async def query_agent(
    request: AgentQueryRequest,
    service: AgentQueryService = Depends(get_agent_service),
) -> AgentQueryResponse:
    """Answer a supply-chain graph question using validated grounded evidence."""
    try:
        explanation = await service.answer(request.question)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc

    payload = explanation.model_dump()
    # Event refs are valid evidence identifiers, but the deterministic explainer
    # does not currently carry all Event source fields into the public response.
    # Mark them PARTIAL instead of fabricating source/timestamp/confidence data.
    payload["provenance"] = [
        EvidenceProvenance(
            event_id=event_ref,
            availability=EvidenceAvailability.PARTIAL,
        )
        for event_ref in explanation.event_refs
    ]
    return AgentQueryResponse(**payload)
