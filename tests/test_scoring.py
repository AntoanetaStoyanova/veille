from datetime import UTC, datetime, timedelta

import pytest

from tests.helpers import make_llm
from veille.bin.collect import Article
from veille.bin.scoring import ScoredArticle, score_articles, select_top
from veille.config.settings import MODEL_SCORING

BASE = datetime(2026, 11, 20, tzinfo=UTC)


def _article(n: int, age_hours: int = 0) -> Article:
    return Article(
        title=f"Titre {n}",
        url=f"https://a.com/{n}",
        source="Blog",
        theme="ia",
        published=BASE - timedelta(hours=age_hours),
        excerpt="extrait",
    )


def test_score_articles_associe_chaque_note_a_son_article() -> None:
    articles = [_article(1), _article(2)]
    llm = make_llm({"https://a.com/1": 4, "https://a.com/2": 2})

    scored = score_articles(articles, llm)

    assert [(s.article.url, s.score) for s in scored] == [
        ("https://a.com/1", 4),
        ("https://a.com/2", 2),
    ]


def test_score_articles_envoie_un_seul_appel_avec_tous_les_articles() -> None:
    llm = make_llm({"https://a.com/1": 3, "https://a.com/2": 3})

    score_articles([_article(1), _article(2)], llm)

    llm.assert_called_once()
    model, prompt = llm.call_args.args
    assert model == MODEL_SCORING
    assert "https://a.com/1" in prompt and "https://a.com/2" in prompt


def test_score_articles_sans_candidat_n_appelle_pas_le_modele() -> None:
    llm = make_llm({})

    assert score_articles([], llm) == []
    llm.assert_not_called()


def test_score_articles_url_absente_leve_une_erreur() -> None:
    llm = make_llm({"https://a.com/1": 4})

    with pytest.raises(ValueError, match="a.com/2"):
        score_articles([_article(1), _article(2)], llm)


@pytest.mark.parametrize("note", [0, 6, 3.5, "4", True])
def test_score_articles_note_invalide_leve_une_erreur(note: object) -> None:
    llm = make_llm({"https://a.com/1": note})

    with pytest.raises(ValueError, match="invalide"):
        score_articles([_article(1)], llm)


def test_select_top_trie_par_note_et_garde_n_articles() -> None:
    scored = [ScoredArticle(_article(i), s) for i, s in enumerate([2, 5, 3, 4])]

    top = select_top(scored, n=3)

    assert [s.score for s in top] == [5, 4, 3]


def test_select_top_met_a_la_une_la_meilleure_note() -> None:
    scored = [ScoredArticle(_article(i), s) for i, s in enumerate([3, 5, 4])]

    assert select_top(scored)[0].article.url == "https://a.com/1"


def test_select_top_departage_les_egalites_par_la_date() -> None:
    old = ScoredArticle(_article(1, age_hours=48), 5)
    recent = ScoredArticle(_article(2, age_hours=1), 5)

    assert select_top([old, recent])[0] is recent
