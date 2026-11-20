"""Orchestration du pipeline de veille."""

from veille.config.settings import PROJECT_NAME
from veille.log import setup_logging


def main() -> None:
    """Point d'entrée du pipeline."""
    logger = setup_logging(PROJECT_NAME)
    logger.info("Starting %s", PROJECT_NAME)
