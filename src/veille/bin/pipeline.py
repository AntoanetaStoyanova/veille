"""Orchestration du pipeline de veille."""

import argparse
import logging
from collections.abc import Callable, Sequence
from datetime import date
from pathlib import Path

import feedparser

from veille.bin.collect import Parser, fetch_articles
from veille.bin.llm import LLM, ask_json
from veille.bin.mail import MailSettings, load_mail_settings, render, send
from veille.bin.prefilter import normalize_url, prefilter
from veille.bin.scoring import score_articles, select_top
from veille.bin.summarize import summarize
from veille.config import load_sources
from veille.config.settings import PROJECT_NAME, SEEN_PATH
from veille.data.seen import load_seen, prune, save_seen
from veille.log import setup_logging

logger = logging.getLogger(__name__)

Mailer = Callable[[str, str, str, MailSettings], None]


def run(
    dry_run: bool = False,
    *,
    llm: LLM = ask_json,
    parse: Parser = feedparser.parse,
    mailer: Mailer = send,
    seen_path: Path = SEEN_PATH,
    today: date | None = None,
) -> None:
    """
    Enchaîne collecte, filtre, tri, résumé et envoi du mail du jour.

    L'historique n'est mis à jour qu'après un envoi réussi.

    Parameters
    ----------
    dry_run : bool
        Si vrai, journalise le mail sans l'envoyer ni écrire l'historique.
    llm : LLM
        Fonction d'appel au modèle (`veille.bin.llm.ask_json` par défaut).
    parse : Parser
        Lecteur de flux (`feedparser.parse` par défaut).
    mailer : Mailer
        Fonction d'envoi (`veille.bin.mail.send` par défaut).
    seen_path : Path
        Fichier de l'historique.
    today : date | None
        Jour de la veille ; aujourd'hui par défaut.

    Raises
    ------
    ValueError
        Si une variable d'environnement du mail manque (hors `dry_run`) ou si
        une réponse de Claude est inexploitable.
    """
    today = today or date.today()
    # Avant les appels payants : un secret manquant doit échouer tout de suite.
    settings = None if dry_run else load_mail_settings()

    themes = load_sources()
    seen = prune(load_seen(seen_path), today)
    candidates = prefilter(fetch_articles(themes, parse=parse), seen, themes)
    if not candidates:
        logger.info("Aucun nouvel article : pas de mail envoyé")
        return

    top = select_top(score_articles(candidates, llm))
    digest = summarize([s.article for s in top], llm)
    subject, html, text = render(digest, themes, today)

    if settings is None:
        logger.info("Dry run, mail non envoyé :\n%s", text)
        return

    mailer(subject, html, text, settings)
    items = [digest.headline, *digest.others]
    seen.update({normalize_url(i.article.url): today for i in items})
    save_seen(seen_path, seen)
    logger.info("Mail envoyé : %s", subject)


def main(argv: Sequence[str] | None = None) -> None:
    """
    Point d'entrée en ligne de commande.

    Parameters
    ----------
    argv : Sequence[str] | None
        Arguments ; `sys.argv[1:]` par défaut.
    """
    parser = argparse.ArgumentParser(prog=PROJECT_NAME, description=__doc__)
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="affiche le mail sans l'envoyer ni modifier l'historique",
    )
    args = parser.parse_args(argv)
    setup_logging(PROJECT_NAME)
    run(dry_run=args.dry_run)
