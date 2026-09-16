from functools import lru_cache

from fastapi import HTTPException, status

from src.api.services.agent import AgentQueryService
from src.api.services.companies import CompanyGraphService
from src.api.services.events import EventReadService
from src.api.services.risk import RiskAnalyticsService
from src.config.settings import Settings, settings
from src.events.read_repository import EventReadRepository
from src.graph.company_repository import CompanyGraphRepository
from src.graph.connection import Neo4jConnection
from src.risk.repository import RiskRepository


def get_settings() -> Settings:
    return settings


@lru_cache(maxsize=1)
def get_neo4j_connection() -> Neo4jConnection:
    return Neo4jConnection()


def get_company_repository() -> CompanyGraphRepository:
    return CompanyGraphRepository(get_neo4j_connection())


def get_company_service() -> CompanyGraphService:
    return CompanyGraphService(get_company_repository())


def get_event_repository() -> EventReadRepository:
    return EventReadRepository(get_neo4j_connection())


def get_event_service() -> EventReadService:
    return EventReadService(get_event_repository())


def get_risk_repository() -> RiskRepository:
    return RiskRepository(get_neo4j_connection())


def get_risk_service() -> RiskAnalyticsService:
    return RiskAnalyticsService(get_risk_repository())


def get_agent_service() -> AgentQueryService:
    """Resolve the public agent service once a production StructuredLLM exists."""
    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail="Agentic RAG provider is not configured.",
    )


def close_neo4j_connection() -> None:
    if get_neo4j_connection.cache_info().currsize:
        get_neo4j_connection().close()
        get_neo4j_connection.cache_clear()
