"""Constantes du pipeline de veille."""

from pathlib import Path

PROJECT_NAME = "veille"

SOURCES_PATH = Path(__file__).parent / "sources.yml"

MODEL_SCORING = "claude-haiku-5-5"
MODEL_SUMMARY = "claude-sonnet-5-5"

SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 465

FRESHNESS_DAYS = 3
MAX_CANDIDATES = 40
MAX_ITEMS = 8
SEEN_RETENTION_DAYS = 90

INTEREST_PROFILE = (
    "Profil : data engineering avec Python et dbt. Intérêts : nouveautés de l'IA "
    "(modèles, outils, recherche appliquée), automatisation avec l'IA (agents, "
    "workflows, MCP), dbt et analytics engineering, Python (langage, outillage, "
    "bibliothèques). Préfère les annonces concrètes, les versions utiles et les "
    "retours d'expérience au marketing et aux opinions."
)
