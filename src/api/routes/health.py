from fastapi import APIRouter, Depends

from src.api.dependencies import get_neo4j_connection, get_settings
from src.api.schemas import DetailedHealthResponse, ServiceHealth
from src.config.settings import Settings


router = APIRouter(tags=["system"])


@router.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "healthy"}


@router.get("/api/v1/health/detailed", response_model=DetailedHealthResponse)
def detailed_health(settings: Settings = Depends(get_settings)) -> DetailedHealthResponse:
    services: dict[str, ServiceHealth] = {}
    try:
        connection = get_neo4j_connection()
        with connection.driver.session() as session:
            session.run("RETURN 1 AS ok").single()
        services["neo4j"] = ServiceHealth(status="healthy")
    except Exception as exc:
        services["neo4j"] = ServiceHealth(status="unhealthy", detail=type(exc).__name__)

    provider = settings.LLM_PROVIDER.strip().lower()
    if provider == "openai" and settings.LLM_API_KEY.strip() and settings.LLM_MODEL.strip():
        services["agent_llm"] = ServiceHealth(status="configured")
    else:
        services["agent_llm"] = ServiceHealth(status="unconfigured", detail="Set LLM_PROVIDER=openai, LLM_API_KEY, and LLM_MODEL.")

    overall = "healthy" if services["neo4j"].status == "healthy" else "degraded"
    return DetailedHealthResponse(status=overall, services=services)


@router.get("/api/v1/info")
def get_info(settings: Settings = Depends(get_settings)) -> dict[str, str]:
    return {"app_name": settings.APP_NAME, "environment": settings.APP_ENV}
