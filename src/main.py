"""
Main application entry point.
"""

import logging
import sys

from src.config.logging import setup_logging
from src.config.settings import settings
from src.config.validation import validate_application_config


def main() -> None:
    """
    Initialize and start the application.
    """

    setup_logging()

    logger = logging.getLogger("main")

    logger.info("Starting %s", settings.APP_NAME)
    logger.info("Environment: %s", settings.APP_ENV)
    logger.info("Debug mode: %s", settings.DEBUG)

    # --------------------------------------------
    # Validate core configuration
    # --------------------------------------------

    configuration_errors = validate_application_config()

    if configuration_errors:
        logger.error("Configuration validation failed:")

        for error in configuration_errors:
            logger.error("- %s", error)

        sys.exit(1)

    logger.info("Core configuration validated successfully")

    # --------------------------------------------
    # Report optional integrations
    # --------------------------------------------

    logger.info(
        "Neo4j database configured: %s",
        bool(settings.NEO4J_DATABASE),
    )

    logger.info(
        "News API configured: %s",
        bool(settings.NEWS_API_KEY),
    )

    logger.info(
        "SEC EDGAR configured: %s",
        bool(settings.SEC_USER_AGENT),
    )

    logger.info(
        "LLM provider configured: %s",
        bool(settings.LLM_PROVIDER),
    )

    logger.info("Application initialization complete")


if __name__ == "__main__":
    main()