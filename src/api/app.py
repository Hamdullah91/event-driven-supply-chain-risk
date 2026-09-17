from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.api.dependencies import close_neo4j_connection, get_neo4j_connection
from src.api.routes.agent import router as agent_router
from src.api.routes.companies import router as companies_router, search_router
from src.api.routes.events import router as events_router
from src.api.routes.health import router as health_router
from src.api.routes.risk import router as risk_router
from src.api.routes.websocket import router as websocket_router
from src.config.settings import settings
from src.ingestion.news.runtime import news_poller_runtime


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    try:
        await news_poller_runtime.start(
            settings=settings,
            connection=get_neo4j_connection(),
        )
        yield
    finally:
        await news_poller_runtime.stop()
        close_neo4j_connection()


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.APP_NAME,
        version="0.1.0",
        description="Backend API for event-driven supply chain risk intelligence.",
        lifespan=lifespan,
    )
    app.include_router(health_router)
    app.include_router(events_router)
    app.include_router(companies_router)
    app.include_router(search_router)
    app.include_router(risk_router)
    app.include_router(agent_router)
    app.include_router(websocket_router)
    return app


app = create_app()
