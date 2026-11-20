"""Constantes du pipeline de veille."""

from pathlib import Path

PROJECT_NAME = "veille"

SOURCES_PATH = Path(__file__).parent / "sources.yml"

MODEL_SCORING = "claude-haiku-5-5"
MODEL_SUMMARY = "claude-sonnet-5-5"

FRESHNESS_DAYS = 3
MAX_CANDIDATES = 40
MAX_ITEMS = 8
SEEN_RETENTION_DAYS = 90
