from fastapi import FastAPI

from src.api.routes.events import router as events_router
from src.api.routes.health import router as health_router
from src.config.settings import settings


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.APP_NAME,
        version="0.1.0",
        description="Backend API for event-driven supply chain risk intelligence.",
    )
    app.include_router(health_router)
    app.include_router(events_router)
    return app


app = create_app()
