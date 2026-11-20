"""Notation de la pertinence des articles par Claude Haiku."""

import json
from collections.abc import Sequence
from dataclasses import dataclass

import anthropic

from veille.bin.collect import Article
from veille.config.settings import INTEREST_PROFILE, MAX_ITEMS, MODEL_SCORING

SCORING_MAX_TOKENS = 2000
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


def score_articles(
    articles: Sequence[Article], client: anthropic.Anthropic
) -> list[ScoredArticle]:
    """
    Note tous les articles en un seul appel à Haiku.

    Parameters
    ----------
    articles : Sequence[Article]
        Candidats à noter.
    client : anthropic.Anthropic
        Client de l'API Anthropic.

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

    response = client.messages.create(
        model=MODEL_SCORING,
        max_tokens=SCORING_MAX_TOKENS,
        messages=[{"role": "user", "content": _build_prompt(articles)}],
    )
    text = "".join(b.text for b in response.content if b.type == "text")
    try:
        notes = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Réponse de notation non JSON : {text[:200]!r}") from exc
    if not isinstance(notes, dict):
        raise ValueError(f"Réponse de notation inattendue : {text[:200]!r}")

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
