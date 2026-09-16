from fastapi import APIRouter, Depends, HTTPException, status

from src.api.dependencies import get_agent_service
from src.api.schemas import AgentQueryRequest, AgentQueryResponse
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
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc

    return AgentQueryResponse(**explanation.model_dump())
