"""
Application configuration and environment settings.
"""

import os

from dotenv import load_dotenv


# Load environment variables from .env
load_dotenv()


class Settings:
    """Centralized application configuration."""

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

    NEO4J_URI: str = os.getenv("NEO4J_URI", "")
    NEO4J_USERNAME: str = os.getenv("NEO4J_USERNAME", "")
    NEO4J_PASSWORD: str = os.getenv("NEO4J_PASSWORD", "")
    NEO4J_DATABASE: str = os.getenv("NEO4J_DATABASE", "neo4j")

    # ============================================
    # News / Event Ingestion
    # ============================================

    NEWS_API_KEY: str = os.getenv("NEWS_API_KEY", "")
    NEWS_API_URL: str = os.getenv(
        "NEWS_API_URL",
        "https://newsapi.org/v2/everything",
    )
    NEWS_POLLER_ENABLED: bool = os.getenv(
        "NEWS_POLLER_ENABLED",
        "false",
    ).lower() == "true"
    NEWS_POLL_INTERVAL_SECONDS: int = int(
        os.getenv("NEWS_POLL_INTERVAL_SECONDS", "900")
    )
    NEWS_REQUEST_TIMEOUT_SECONDS: float = float(
        os.getenv("NEWS_REQUEST_TIMEOUT_SECONDS", "20.0")
    )
    NEWS_MAX_RETRIES: int = int(os.getenv("NEWS_MAX_RETRIES", "4"))
    NEWS_DATABASE_PATH: str = os.getenv(
        "NEWS_DATABASE_PATH",
        "data/news/news.db",
    )
    EVENT_CLASSIFIER_MODEL_PATH: str = os.getenv(
        "EVENT_CLASSIFIER_MODEL_PATH",
        "models/event_classifier/distilbert_supply_chain",
    )
    EVENT_CLASSIFIER_MAX_LENGTH: int = int(
        os.getenv("EVENT_CLASSIFIER_MAX_LENGTH", "256")
    )
    EVENT_CLASSIFIER_CONFIDENCE_THRESHOLD: float = float(
        os.getenv("EVENT_CLASSIFIER_CONFIDENCE_THRESHOLD", "0.70")
    )

    # ============================================
    # SEC EDGAR
    # ============================================

    SEC_USER_AGENT: str = os.getenv("SEC_USER_AGENT", "")

    # ============================================
    # LLM / Agentic RAG
    # ============================================

    # Supported production providers: gemini and openai.
    # Gemini 3.5 Flash-Lite is the default because it is a stable, cost-efficient
    # model suitable for structured planner/Cypher calls and is available on the
    # Gemini API free tier for eligible projects.
    # LLM_API_KEY must always be supplied through the local environment.
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "gemini")
    LLM_API_KEY: str = os.getenv("LLM_API_KEY", "")
    LLM_MODEL: str = os.getenv("LLM_MODEL", "gemini-3.5-flash-lite")

    # ============================================
    # API
    # ============================================

    API_HOST: str = os.getenv("API_HOST", "127.0.0.1")
    API_PORT: int = int(os.getenv("API_PORT", "8000"))


settings = Settings()
