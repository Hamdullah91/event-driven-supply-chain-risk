"""
Application configuration and environment settings.
"""

import os

from dotenv import load_dotenv


# Load environment variables from .env
load_dotenv()


class Settings:
    """
    Centralized application configuration.
    """

    # ============================================
    # Application
    # ============================================

    APP_NAME: str = os.getenv(
        "APP_NAME",
        "Event-Driven Supply Chain Risk Intelligence",
    )

    APP_ENV: str = os.getenv(
        "APP_ENV",
        "development",
    )

    DEBUG: bool = os.getenv(
        "DEBUG",
        "false",
    ).lower() == "true"

    # ============================================
    # Neo4j Knowledge Graph
    # ============================================

    NEO4J_URI: str = os.getenv(
        "NEO4J_URI",
        "",
    )

    NEO4J_USERNAME: str = os.getenv(
        "NEO4J_USERNAME",
        "",
    )

    NEO4J_PASSWORD: str = os.getenv(
        "NEO4J_PASSWORD",
        "",
    )

    NEO4J_DATABASE: str = os.getenv(
        "NEO4J_DATABASE",
        "neo4j",
    )

    # ============================================
    # News / Event Ingestion
    # ============================================

    NEWS_API_KEY: str = os.getenv(
        "NEWS_API_KEY",
        "",
    )

    # ============================================
    # SEC EDGAR
    # ============================================

    SEC_USER_AGENT: str = os.getenv(
        "SEC_USER_AGENT",
        "",
    )

    # ============================================
    # LLM / Agentic RAG
    # ============================================

    LLM_PROVIDER: str = os.getenv(
        "LLM_PROVIDER",
        "",
    )

    LLM_API_KEY: str = os.getenv(
        "LLM_API_KEY",
        "",
    )

    LLM_MODEL: str = os.getenv(
        "LLM_MODEL",
        "",
    )

    # ============================================
    # API
    # ============================================

    API_HOST: str = os.getenv(
        "API_HOST",
        "127.0.0.1",
    )

    API_PORT: int = int(
        os.getenv(
            "API_PORT",
            "8000",
        )
    )


settings = Settings()