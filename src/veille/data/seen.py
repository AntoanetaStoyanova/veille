"""Historique des articles déjà envoyés."""

import json
import os
from collections.abc import Mapping
from datetime import date, timedelta
from pathlib import Path

from veille.config.settings import SEEN_RETENTION_DAYS


def load_seen(path: Path) -> dict[str, date]:
    """
    Charge l'historique `{url: date_envoi}`.

    Parameters
    ----------
    path : Path
        Fichier JSON de l'historique.

    Returns
    -------
    dict[str, date]
        Historique ; vide si le fichier n'existe pas.
    """
    if not path.exists():
        return {}
    raw = json.loads(path.read_text(encoding="utf-8"))
    return {url: date.fromisoformat(sent) for url, sent in raw.items()}


def save_seen(path: Path, seen: Mapping[str, date]) -> None:
    """
    Écrit l'historique de façon atomique.

    Parameters
    ----------
    path : Path
        Fichier JSON de l'historique.
    seen : Mapping[str, date]
        Historique `{url: date_envoi}`.
    """
    raw = {url: sent.isoformat() for url, sent in sorted(seen.items())}
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(raw, indent=2) + "\n", encoding="utf-8")
    os.replace(tmp, path)


def prune(seen: Mapping[str, date], today: date) -> dict[str, date]:
    """
    Retire les entrées plus anciennes que `SEEN_RETENTION_DAYS` jours.

    Parameters
    ----------
    seen : Mapping[str, date]
        Historique `{url: date_envoi}`.
    today : date
        Jour de référence.

    Returns
    -------
    dict[str, date]
        Historique purgé.
    """
    oldest = today - timedelta(days=SEEN_RETENTION_DAYS)
    return {url: sent for url, sent in seen.items() if sent >= oldest}
