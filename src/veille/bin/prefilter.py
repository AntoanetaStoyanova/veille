"""Pré-filtre des articles avant la notation par le LLM."""

import re
from collections.abc import Iterable, Mapping
from datetime import date
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from veille.bin.collect import Article
from veille.config import Theme
from veille.config.settings import MAX_CANDIDATES


def normalize_url(url: str) -> str:
    """
    Normalise une URL pour comparer deux liens vers le même article.

    Parameters
    ----------
    url : str
        URL brute.

    Returns
    -------
    str
        URL sans fragment, sans paramètres `utm_*`, sans `/` final, hôte en
        minuscules.

    Examples
    --------
    >>> normalize_url("https://Example.com/post/?utm_source=x&id=1#top")
    'https://example.com/post?id=1'
    """
    parts = urlsplit(url)
    query = [(k, v) for k, v in parse_qsl(parts.query) if not k.startswith("utm_")]
    return urlunsplit(
        (
            parts.scheme.lower(),
            parts.netloc.lower(),
            parts.path.rstrip("/"),
            urlencode(query),
            "",
        )
    )


def drop_seen(articles: Iterable[Article], seen: Mapping[str, date]) -> list[Article]:
    """
    Retire les articles déjà envoyés.

    Parameters
    ----------
    articles : Iterable[Article]
        Articles collectés.
    seen : Mapping[str, date]
        Historique dont les clés sont des URL normalisées.

    Returns
    -------
    list[Article]
        Articles dont l'URL normalisée n'est pas dans l'historique.
    """
    return [a for a in articles if normalize_url(a.url) not in seen]


def drop_duplicates(articles: Iterable[Article]) -> list[Article]:
    """
    Retire les doublons d'URL normalisée, en gardant la première occurrence.

    Parameters
    ----------
    articles : Iterable[Article]
        Articles collectés.

    Returns
    -------
    list[Article]
        Articles à URL unique, dans l'ordre d'origine.
    """
    unique: dict[str, Article] = {}
    for article in articles:
        unique.setdefault(normalize_url(article.url), article)
    return list(unique.values())


def keyword_filter(
    articles: Iterable[Article], themes: Iterable[Theme]
) -> list[Article]:
    """
    Garde les articles qui contiennent un mot-clé de leur thème.

    Parameters
    ----------
    articles : Iterable[Article]
        Articles collectés.
    themes : Iterable[Theme]
        Thèmes et leurs mots-clés.

    Returns
    -------
    list[Article]
        Articles dont le titre, la source ou l'extrait contient un mot-clé.
    """
    patterns = {
        theme.key: re.compile(
            r"\b(?:" + "|".join(re.escape(k) for k in theme.keywords) + r")\b"
        )
        for theme in themes
    }
    # La source est incluse : un titre de release ("v1.8.0") ne cite pas le sujet.
    return [
        a
        for a in articles
        if patterns[a.theme].search(f"{a.title} {a.source} {a.excerpt}".lower())
    ]


def prefilter(
    articles: Iterable[Article],
    seen: Mapping[str, date],
    themes: Iterable[Theme],
    limit: int = MAX_CANDIDATES,
) -> list[Article]:
    """
    Enchaîne historique, doublons, mots-clés et plafond de candidats.

    Parameters
    ----------
    articles : Iterable[Article]
        Articles collectés.
    seen : Mapping[str, date]
        Historique dont les clés sont des URL normalisées.
    themes : Iterable[Theme]
        Thèmes et leurs mots-clés.
    limit : int
        Nombre maximal de candidats.

    Returns
    -------
    list[Article]
        Les `limit` articles les plus récents parmi ceux retenus.
    """
    kept = keyword_filter(drop_duplicates(drop_seen(articles, seen)), themes)
    return sorted(kept, key=lambda a: a.published, reverse=True)[:limit]
