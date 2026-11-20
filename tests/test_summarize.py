import json
from datetime import UTC, datetime

import pytest

from tests.helpers import make_client
from veille.bin.collect import Article
from veille.bin.summarize import summarize
from veille.config.settings import MODEL_SUMMARY


def _article(n: int) -> Article:
    return Article(
        title=f"Titre {n}",
        url=f"https://a.com/{n}",
        source="Blog",
        theme="ia",
        published=datetime(2026, 11, 20, tzinfo=UTC),
        excerpt="extrait",
    )


def _entry(n: int) -> dict[str, str]:
    return {
        "ce_qui_se_passe": f"faits {n}",
        "pourquoi_important": f"impact {n}",
        "explique_simplement": f"image {n}",
    }


def test_summarize_remplit_les_trois_blocs_de_chaque_item() -> None:
    reply = {f"https://a.com/{n}": _entry(n) for n in (1, 2, 3)}
    client = make_client(json.dumps(reply))

    digest = summarize([_article(1), _article(2), _article(3)], client)

    assert digest.headline.article.url == "https://a.com/1"
    assert [i.article.url for i in digest.others] == [
        "https://a.com/2",
        "https://a.com/3",
    ]
    for n, item in enumerate((digest.headline, *digest.others), start=1):
        assert item.what_happens == f"faits {n}"
        assert item.why_important == f"impact {n}"
        assert item.explained_simply == f"image {n}"


def test_summarize_envoie_un_seul_appel_a_sonnet_avec_tous_les_articles() -> None:
    reply = {f"https://a.com/{n}": _entry(n) for n in (1, 2)}
    client = make_client(json.dumps(reply))

    summarize([_article(1), _article(2)], client)

    client.messages.create.assert_called_once()
    kwargs = client.messages.create.call_args.kwargs
    prompt = kwargs["messages"][0]["content"]
    assert kwargs["model"] == MODEL_SUMMARY
    assert "Titre 1" in prompt and "Titre 2" in prompt


def test_summarize_item_manquant_leve_une_erreur() -> None:
    client = make_client(json.dumps({"https://a.com/1": _entry(1)}))

    with pytest.raises(ValueError, match="a.com/2"):
        summarize([_article(1), _article(2)], client)


@pytest.mark.parametrize("missing", ["ce_qui_se_passe", "explique_simplement"])
def test_summarize_bloc_absent_ou_vide_leve_une_erreur(missing: str) -> None:
    for broken in ({**_entry(1), missing: "  "}, {**_entry(1)} | {missing: None}):
        client = make_client(json.dumps({"https://a.com/1": broken}))

        with pytest.raises(ValueError, match="incomplet"):
            summarize([_article(1)], client)


def test_summarize_reponse_non_json_leve_une_erreur() -> None:
    with pytest.raises(ValueError, match="JSON"):
        summarize([_article(1)], make_client("pas du json"))
