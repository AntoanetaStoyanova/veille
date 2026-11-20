"""Collecte des articles depuis les flux RSS et Atom."""

import calendar
import html
import logging
import re
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any

import feedparser

from veille.config import Feed, Theme
from veille.config.settings import FRESHNESS_DAYS

logger = logging.getLogger(__name__)

EXCERPT_MAX_CHARS = 500

Parser = Callable[[str], Any]  # FeedParserDict, non typé par feedparser


@dataclass(frozen=True)
class Article:
    """
    Article collecté.

    Attributes
    ----------
    title : str
        Titre de l'article.
    url : str
        Lien de l'article.
    source : str
        Nom du flux d'origine.
    theme : str
        Clé du thème du flux.
    published : datetime
        Date de publication (UTC).
    excerpt : str
        Début du texte, sans balises HTML.
    """

    title: str
    url: str
    source: str
    theme: str
    published: datetime
    excerpt: str


def _clean_excerpt(raw: str) -> str:
    """Retire les balises HTML, normalise les espaces et tronque."""
    text = html.unescape(re.sub(r"<[^>]+>", " ", raw))
    return " ".join(text.split())[:EXCERPT_MAX_CHARS]


def _published(entry: Any) -> datetime | None:
    """Date UTC de l'entrée, ou `None` si le flux n'en donne pas."""
    parsed = entry.get("published_parsed") or entry.get("updated_parsed")
    return datetime.fromtimestamp(calendar.timegm(parsed), UTC) if parsed else None


def _fetch_feed(
    feed: Feed, theme: Theme, cutoff: datetime, parse: Parser
) -> list[Article]:
    """Articles récents d'un flux ; liste vide si le flux est illisible."""
    parsed = parse(feed.url)
    if parsed.bozo and not parsed.entries:
        logger.warning("Flux ignoré (%s) : %s", feed.name, parsed.bozo_exception)
        return []

    articles = []
    for entry in parsed.entries:
        published = _published(entry)
        url = entry.get("link")
        if url is None or published is None or published < cutoff:
            continue
        articles.append(
            Article(
                title=entry.get("title", "").strip(),
                url=url,
                source=feed.name,
                theme=theme.key,
                published=published,
                excerpt=_clean_excerpt(entry.get("summary", "")),
            )
        )
    return articles


def fetch_articles(
    themes: Iterable[Theme],
    now: datetime | None = None,
    parse: Parser = feedparser.parse,
) -> list[Article]:
    """
    Collecte les articles récents de tous les flux.

    Un flux illisible est ignoré avec un avertissement, sans interrompre les autres.

    Parameters
    ----------
    themes : Iterable[Theme]
        Thèmes et flux à lire.
    now : datetime | None
        Instant de référence de la fenêtre de fraîcheur ; maintenant par défaut.
    parse : Parser
        Fonction qui lit un flux depuis son URL (`feedparser.parse` par défaut).

    Returns
    -------
    list[Article]
        Articles publiés depuis moins de `FRESHNESS_DAYS` jours.
    """
    cutoff = (now or datetime.now(UTC)) - timedelta(days=FRESHNESS_DAYS)
    return [
        article
        for theme in themes
        for feed in theme.feeds
        for article in _fetch_feed(feed, theme, cutoff, parse)
    ]
