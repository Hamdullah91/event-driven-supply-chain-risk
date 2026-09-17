from pathlib import Path

from fastapi import APIRouter, Depends

from src.api.dependencies import get_neo4j_connection, get_settings
from src.api.schemas import DetailedHealthResponse, ServiceHealth
from src.api.websocket import risk_connection_manager
from src.config.settings import Settings
from src.ingestion.news.runtime import news_poller_runtime


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
        services["neo4j"] = ServiceHealth(
            status="unhealthy",
            detail=type(exc).__name__,
        )

    provider = settings.LLM_PROVIDER.strip().lower()
    if provider == "openai" and settings.LLM_API_KEY.strip() and settings.LLM_MODEL.strip():
        services["agent_llm"] = ServiceHealth(status="configured")
    else:
        services["agent_llm"] = ServiceHealth(
            status="unconfigured",
            detail="Set LLM_PROVIDER=openai, LLM_API_KEY, and LLM_MODEL.",
        )

    services["websocket"] = ServiceHealth(
        status="available",
        detail=(
            "In-process risk stream manager is available; "
            f"active_connections={len(risk_connection_manager.active_connections)}."
        ),
    )

    poller = news_poller_runtime.snapshot()
    poller_detail = poller.get("last_error")
    if not poller_detail:
        poller_detail = (
            "Same-process poller is disabled by configuration."
            if poller["status"] == "disabled"
            else "Same-process poller runtime status."
        )
    services["event_poller"] = ServiceHealth(
        status=str(poller["status"]),
        detail=str(poller_detail),
    )

    model_path = Path(settings.EVENT_CLASSIFIER_MODEL_PATH)
    services["event_classifier"] = ServiceHealth(
        status="available" if model_path.exists() else "unavailable",
        detail=f"model_path={model_path}",
    )

    services["news_api"] = ServiceHealth(
        status="configured" if settings.NEWS_API_KEY.strip() else "unconfigured",
        detail=(
            "NEWS_API_KEY is configured."
            if settings.NEWS_API_KEY.strip()
            else "NEWS_API_KEY is not configured."
        ),
    )

    degraded = services["neo4j"].status != "healthy"
    if settings.NEWS_POLLER_ENABLED and services["event_poller"].status in {
        "failed",
        "unconfigured",
    }:
        degraded = True

    return DetailedHealthResponse(
        status="degraded" if degraded else "healthy",
        services=services,
    )


@router.get("/api/v1/info")
def get_info(settings: Settings = Depends(get_settings)) -> dict[str, str]:
    return {
        "app_name": settings.APP_NAME,
        "environment": settings.APP_ENV,
    }
