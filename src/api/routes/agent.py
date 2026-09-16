from fastapi import APIRouter, Depends, HTTPException, status

from src.api.dependencies import get_agent_service
from src.api.schemas import AgentQueryRequest, AgentQueryResponse, EvidenceProvenance
from src.api.services.agent import AgentQueryService


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
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc

    payload = explanation.model_dump()
    # Event refs are explicit graph evidence identifiers. Keep provenance typed at
    # the public boundary without inventing source metadata not present in the explanation.
    payload["provenance"] = [EvidenceProvenance(event_id=event_ref) for event_ref in explanation.event_refs]
    return AgentQueryResponse(**payload)
