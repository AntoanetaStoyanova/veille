"""Résumé détaillé en français des articles retenus par Claude Sonnet."""

from collections.abc import Sequence
from dataclasses import dataclass

from veille.bin.collect import Article
from veille.bin.llm import LLM
from veille.config.settings import MODEL_SUMMARY

BLOCKS = ("ce_qui_se_passe", "pourquoi_important", "explique_simplement")


@dataclass(frozen=True)
class DigestItem:
    """
    Article accompagné de son explication en français.

    Attributes
    ----------
    article : Article
        Article résumé.
    what_happens : str
        Bloc « Ce qui se passe ».
    why_important : str
        Bloc « Pourquoi c'est important ».
    explained_simply : str
        Bloc « Expliqué simplement ».
    """

    article: Article
    what_happens: str
    why_important: str
    explained_simply: str


@dataclass(frozen=True)
class Digest:
    """
    Contenu du mail du jour.

    Attributes
    ----------
    headline : DigestItem
        Item « à la une ».
    others : tuple[DigestItem, ...]
        Autres items, dans l'ordre d'entrée.
    """

    headline: DigestItem
    others: tuple[DigestItem, ...]


def _build_prompt(articles: Sequence[Article]) -> str:
    """Prompt de résumé : consignes de style, format JSON et liste des articles."""
    lines = [
        f"- url: {a.url}\n  titre: {a.title}\n  source: {a.source}\n"
        f"  extrait: {a.excerpt}"
        for a in articles
    ]
    return (
        "Tu rédiges une veille technique quotidienne en français pour une "
        "personne qui lit surtout l'anglais. Pour chaque article, écris environ "
        "100 mots au total, répartis en trois blocs : « ce_qui_se_passe » (les "
        "faits), « pourquoi_important » (l'impact concret), « explique_simplement » "
        "(une explication accessible, avec une image ou un exemple). Garde les "
        "termes techniques en anglais entre parenthèses après leur traduction. "
        "N'invente rien qui ne soit pas dans le titre ou l'extrait.\n\n"
        'Réponds uniquement par un objet JSON {"<url>": {"ce_qui_se_passe": "...", '
        '"pourquoi_important": "...", "explique_simplement": "..."}} contenant '
        "exactement les URL ci-dessous, sans texte autour.\n\nArticles :\n"
        + "\n".join(lines)
    )


def summarize(articles: Sequence[Article], llm: LLM) -> Digest:
    """
    Résume tous les articles en un seul appel à Sonnet.

    Parameters
    ----------
    articles : Sequence[Article]
        Articles retenus, non vide ; le premier est l'item « à la une ».
    llm : LLM
        Fonction d'appel au modèle (`veille.bin.llm.ask_json` en production).

    Returns
    -------
    Digest
        Résumés, dans l'ordre d'entrée.

    Raises
    ------
    ValueError
        Si la réponse n'est pas un JSON ou s'il manque un article ou un bloc.
    """
    data = llm(MODEL_SUMMARY, _build_prompt(articles))

    items = []
    for article in articles:
        entry = data.get(article.url)
        blocks = [entry.get(b) for b in BLOCKS] if isinstance(entry, dict) else []
        texts = [b.strip() for b in blocks if isinstance(b, str)]
        if len(texts) != len(BLOCKS) or not all(texts):
            raise ValueError(f"Résumé absent ou incomplet pour {article.url}")
        items.append(DigestItem(article, *texts))
    return Digest(headline=items[0], others=tuple(items[1:]))
