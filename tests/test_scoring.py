import json
from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock

import anthropic
import pytest
from anthropic.types import Message, TextBlock, Usage

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


def _client(reply: str) -> MagicMock:
    message = Message(
        id="msg_1",
        content=[TextBlock(type="text", text=reply)],
        model=MODEL_SCORING,
        role="assistant",
        stop_reason="end_turn",
        stop_sequence=None,
        type="message",
        usage=Usage(input_tokens=1, output_tokens=1),
    )
    client = MagicMock(spec=anthropic.Anthropic)
    client.messages.create.return_value = message
    return client


def test_score_articles_associe_chaque_note_a_son_article() -> None:
    articles = [_article(1), _article(2)]
    client = _client(json.dumps({"https://a.com/1": 4, "https://a.com/2": 2}))

    scored = score_articles(articles, client)

    assert [(s.article.url, s.score) for s in scored] == [
        ("https://a.com/1", 4),
        ("https://a.com/2", 2),
    ]


def test_score_articles_envoie_un_seul_appel_avec_tous_les_articles() -> None:
    client = _client(json.dumps({"https://a.com/1": 3, "https://a.com/2": 3}))

    score_articles([_article(1), _article(2)], client)

    client.messages.create.assert_called_once()
    kwargs = client.messages.create.call_args.kwargs
    prompt = kwargs["messages"][0]["content"]
    assert kwargs["model"] == MODEL_SCORING
    assert "https://a.com/1" in prompt and "https://a.com/2" in prompt


def test_score_articles_sans_candidat_n_appelle_pas_l_api() -> None:
    client = _client("{}")

    assert score_articles([], client) == []
    client.messages.create.assert_not_called()


def test_score_articles_json_invalide_leve_une_erreur() -> None:
    with pytest.raises(ValueError, match="JSON"):
        score_articles([_article(1)], _client("voici mes notes : 4"))


def test_score_articles_reponse_non_objet_leve_une_erreur() -> None:
    with pytest.raises(ValueError, match="inattendue"):
        score_articles([_article(1)], _client("[4]"))


def test_score_articles_url_absente_leve_une_erreur() -> None:
    client = _client(json.dumps({"https://a.com/1": 4}))

    with pytest.raises(ValueError, match="a.com/2"):
        score_articles([_article(1), _article(2)], client)


@pytest.mark.parametrize("note", [0, 6, 3.5, "4", True])
def test_score_articles_note_invalide_leve_une_erreur(note: object) -> None:
    client = _client(json.dumps({"https://a.com/1": note}))

    with pytest.raises(ValueError, match="invalide"):
        score_articles([_article(1)], client)


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
