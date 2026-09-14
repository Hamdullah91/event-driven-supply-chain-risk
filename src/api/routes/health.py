from fastapi import APIRouter, Depends

from src.api.dependencies import get_settings
from src.config.settings import Settings


router = APIRouter(tags=["system"])


@router.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "healthy"}


@router.get("/api/v1/info")
def get_info(settings: Settings = Depends(get_settings)) -> dict[str, str]:
    return {
        "app_name": settings.APP_NAME,
        "environment": settings.APP_ENV,
    }
