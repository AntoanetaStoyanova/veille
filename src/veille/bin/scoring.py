"""Notation de la pertinence des articles par Claude Haiku."""

from collections.abc import Sequence
from dataclasses import dataclass

from veille.bin.collect import Article
from veille.bin.llm import LLM
from veille.config.settings import INTEREST_PROFILE, MAX_ITEMS, MODEL_SCORING

PROMPT_EXCERPT_CHARS = 300


@dataclass(frozen=True)
class ScoredArticle:
    """
    Article accompagné de sa note de pertinence.

    Attributes
    ----------
    article : Article
        Article noté.
    score : int
        Note de 1 (hors sujet) à 5 (indispensable).
    """

    article: Article
    score: int


def _build_prompt(articles: Sequence[Article]) -> str:
    """Prompt de notation : profil, consigne de format et liste des articles."""
    lines = [
        f"- url: {a.url}\n  titre: {a.title}\n  source: {a.source}\n"
        f"  extrait: {a.excerpt[:PROMPT_EXCERPT_CHARS]}"
        for a in articles
    ]
    return (
        f"{INTEREST_PROFILE}\n\n"
        "Note la pertinence de chaque article pour ce profil, de 1 (hors sujet) "
        "à 5 (indispensable). Réponds uniquement par un objet JSON "
        '{"<url>": <note entière>} contenant exactement les URL ci-dessous, '
        "sans texte autour.\n\nArticles :\n" + "\n".join(lines)
    )


def score_articles(articles: Sequence[Article], llm: LLM) -> list[ScoredArticle]:
    """
    Note tous les articles en un seul appel à Haiku.

    Parameters
    ----------
    articles : Sequence[Article]
        Candidats à noter.
    llm : LLM
        Fonction d'appel au modèle (`veille.bin.llm.ask_json` en production).

    Returns
    -------
    list[ScoredArticle]
        Articles notés, dans l'ordre d'entrée ; vide si aucun candidat.

    Raises
    ------
    ValueError
        Si la réponse n'est pas un JSON `{url: note}` couvrant tous les articles
        avec des notes entières de 1 à 5.
    """
    if not articles:
        return []

    notes = llm(MODEL_SCORING, _build_prompt(articles))
    scored = []
    for article in articles:
        score = notes.get(article.url)
        if type(score) is not int or not 1 <= score <= 5:
            raise ValueError(f"Note invalide ou absente pour {article.url} : {score!r}")
        scored.append(ScoredArticle(article, score))
    return scored


def select_top(
    scored: Sequence[ScoredArticle], n: int = MAX_ITEMS
) -> list[ScoredArticle]:
    """
    Sélectionne les `n` meilleurs articles ; le premier est l'item « à la une ».

    Parameters
    ----------
    scored : Sequence[ScoredArticle]
        Articles notés.
    n : int
        Nombre d'articles à garder.

    Returns
    -------
    list[ScoredArticle]
        Meilleure note d'abord, à note égale le plus récent d'abord.
    """
    ranked = sorted(scored, key=lambda s: (s.score, s.article.published), reverse=True)
    return ranked[:n]
