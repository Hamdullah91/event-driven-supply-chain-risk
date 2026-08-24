"""
Configuration validation utilities.
"""

from src.config.settings import settings


def validate_application_config() -> list[str]:
    """
    Validate the configuration required to start the application.

    Returns:
        A list of configuration errors.
        An empty list means the configuration is valid.
    """

    errors: list[str] = []

    if not settings.APP_NAME:
        errors.append("APP_NAME is not configured.")

    if not settings.APP_ENV:
        errors.append("APP_ENV is not configured.")

    if not settings.API_HOST:
        errors.append("API_HOST is not configured.")

    if settings.API_PORT <= 0 or settings.API_PORT > 65535:
        errors.append("API_PORT must be between 1 and 65535.")

    return errors