"""Chargement de la configuration des sources."""

from dataclasses import dataclass
from pathlib import Path

import yaml

from veille.config.settings import SOURCES_PATH


@dataclass(frozen=True)
class Feed:
    """
    Flux RSS ou Atom.

    Attributes
    ----------
    name : str
        Nom lisible de la source.
    url : str
        URL du flux.
    """

    name: str
    url: str


@dataclass(frozen=True)
class Theme:
    """
    Thème de veille.

    Attributes
    ----------
    key : str
        Identifiant du thème.
    label : str
        Titre de la section dans le mail.
    keywords : tuple[str, ...]
        Mots-clés du pré-filtre, en minuscules.
    feeds : tuple[Feed, ...]
        Flux du thème.
    """

    key: str
    label: str
    keywords: tuple[str, ...]
    feeds: tuple[Feed, ...]


def _parse_feed(theme_key: str, raw: dict[str, str]) -> Feed:
    """Construit un `Feed` ou lève `ValueError` s'il manque le nom ou l'URL."""
    if not raw.get("url") or not raw.get("name"):
        raise ValueError(f"Thème '{theme_key}' : flux sans 'name' ou 'url' : {raw}")
    return Feed(name=raw["name"], url=raw["url"])


def _parse_theme(key: str, raw: dict[str, object]) -> Theme:
    """Construit un `Theme` ou lève `ValueError` s'il est incomplet."""
    feeds = raw.get("feeds")
    keywords = raw.get("keywords")
    label = raw.get("label")
    if not label or not feeds or not keywords:
        raise ValueError(
            f"Thème '{key}' : 'label', 'keywords' et 'feeds' sont obligatoires"
        )
    assert isinstance(feeds, list) and isinstance(keywords, list)
    return Theme(
        key=key,
        label=str(label),
        keywords=tuple(str(k).lower() for k in keywords),
        feeds=tuple(_parse_feed(key, f) for f in feeds),
    )


def load_sources(path: Path = SOURCES_PATH) -> tuple[Theme, ...]:
    """
    Charge les thèmes et leurs flux depuis un fichier YAML.

    Parameters
    ----------
    path : Path
        Chemin du fichier `sources.yml`.

    Returns
    -------
    tuple[Theme, ...]
        Thèmes dans l'ordre du fichier.

    Raises
    ------
    ValueError
        Si le fichier n'a pas de thème, ou si un thème ou un flux est incomplet.
    """
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    themes = data.get("themes") if isinstance(data, dict) else None
    if not themes:
        raise ValueError(f"{path} : clé 'themes' absente ou vide")
    return tuple(_parse_theme(key, raw) for key, raw in themes.items())
