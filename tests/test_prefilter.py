from datetime import UTC, date, datetime, timedelta

from veille.bin.collect import Article
from veille.bin.prefilter import (
    drop_duplicates,
    drop_seen,
    keyword_filter,
    normalize_url,
    prefilter,
)
from veille.config import Feed, Theme

BASE = datetime(2026, 11, 20, tzinfo=UTC)
THEMES = (
    Theme("ia", "IA", ("llm", "agent"), (Feed("Blog", "https://b.com/rss"),)),
    Theme("dbt", "dbt", ("dbt",), (Feed("dbt-core releases", "https://d.com"),)),
)


def _article(
    url: str,
    title: str = "Un LLM de plus",
    theme: str = "ia",
    source: str = "Blog",
    age_hours: int = 0,
) -> Article:
    return Article(
        title=title,
        url=url,
        source=source,
        theme=theme,
        published=BASE - timedelta(hours=age_hours),
        excerpt="",
    )


def test_normalize_url_ignore_casse_fragment_utm_et_slash_final() -> None:
    assert normalize_url("HTTPS://Example.com/a/?utm_medium=x&p=2#frag") == (
        "https://example.com/a?p=2"
    )


def test_drop_seen_exclut_une_url_deja_vue_meme_non_normalisee() -> None:
    seen = {"https://a.com/x": date(2026, 11, 1)}
    articles = [_article("https://a.com/x/?utm_source=rss"), _article("https://a.com/y")]

    assert [a.url for a in drop_seen(articles, seen)] == ["https://a.com/y"]


def test_drop_duplicates_supprime_un_doublon_du_lot() -> None:
    articles = [_article("https://a.com/x"), _article("https://a.com/x/#top")]

    assert len(drop_duplicates(articles)) == 1


def test_keyword_filter_garde_les_articles_avec_un_mot_cle_du_theme() -> None:
    articles = [
        _article("https://a.com/1", title="Nouvel agent"),
        _article("https://a.com/2", title="Recette de cuisine"),
        _article("https://a.com/3", title="Un LLMOps de plus"),
    ]

    assert [a.url for a in keyword_filter(articles, THEMES)] == ["https://a.com/1"]


def test_keyword_filter_utilise_les_mots_cles_du_theme_de_l_article() -> None:
    article = _article("https://a.com/1", title="Nouvel agent", theme="dbt")

    assert keyword_filter([article], THEMES) == []


def test_keyword_filter_reconnait_le_sujet_via_la_source() -> None:
    release = _article("https://a.com/r", "v1.8.0", "dbt", "dbt-core releases")

    assert keyword_filter([release], THEMES) == [release]


def test_prefilter_plafonne_aux_articles_les_plus_recents() -> None:
    articles = [_article(f"https://a.com/{i}", age_hours=i) for i in range(10)]

    result = prefilter(articles, {}, THEMES, limit=3)

    assert [a.url for a in result] == [f"https://a.com/{i}" for i in range(3)]
