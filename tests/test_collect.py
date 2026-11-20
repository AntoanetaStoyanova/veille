import logging
from datetime import UTC, datetime
from typing import Any

import feedparser
import pytest

from veille.bin.collect import fetch_articles
from veille.config import Feed, Theme

NOW = datetime(2026, 11, 20, 8, 0, tzinfo=UTC)

RSS = """<?xml version="1.0"?>
<rss version="2.0"><channel><title>Blog</title>
  <item>
    <title> Nouveau modèle </title>
    <link>https://example.com/rss-recent</link>
    <description>&lt;p&gt;Un &lt;b&gt;gros&lt;/b&gt;   modèle&lt;/p&gt;</description>
    <pubDate>Thu, 19 Nov 2026 08:00:00 GMT</pubDate>
  </item>
  <item>
    <title>Vieil article</title>
    <link>https://example.com/rss-old</link>
    <pubDate>Sun, 01 Nov 2026 08:00:00 GMT</pubDate>
  </item>
</channel></rss>"""

ATOM = """<?xml version="1.0"?>
<feed xmlns="http://www.w3.org/2005/Atom"><title>Releases</title>
  <entry>
    <title>v1.2.0</title>
    <link href="https://example.com/atom-recent"/>
    <updated>2026-11-18T10:30:00Z</updated>
    <summary>Notes de version</summary>
  </entry>
</feed>"""

CONTENTS = {
    "https://example.com/rss": RSS,
    "https://example.com/atom": ATOM,
    "https://example.com/broken": "ceci n'est pas un flux",
}


def _parse(url: str) -> Any:
    return feedparser.parse(CONTENTS[url])


def _theme(*urls: str) -> Theme:
    feeds = tuple(Feed(name=f"src-{i}", url=u) for i, u in enumerate(urls))
    return Theme(key="ia", label="IA", keywords=("ia",), feeds=feeds)


def test_fetch_articles_parse_un_flux_rss() -> None:
    (article,) = fetch_articles([_theme("https://example.com/rss")], NOW, _parse)

    assert article.title == "Nouveau modèle"
    assert article.url == "https://example.com/rss-recent"
    assert article.source == "src-0"
    assert article.theme == "ia"
    assert article.published == datetime(2026, 11, 19, 8, 0, tzinfo=UTC)
    assert article.excerpt == "Un gros modèle"


def test_fetch_articles_parse_un_flux_atom() -> None:
    (article,) = fetch_articles([_theme("https://example.com/atom")], NOW, _parse)

    assert article.url == "https://example.com/atom-recent"
    assert article.published == datetime(2026, 11, 18, 10, 30, tzinfo=UTC)
    assert article.excerpt == "Notes de version"


def test_fetch_articles_exclut_les_articles_hors_fenetre() -> None:
    articles = fetch_articles([_theme("https://example.com/rss")], NOW, _parse)

    assert "https://example.com/rss-old" not in {a.url for a in articles}


def test_fetch_articles_ignore_un_flux_casse_sans_interrompre_les_autres(
    caplog: pytest.LogCaptureFixture,
) -> None:
    theme = _theme(
        "https://example.com/broken",
        "https://example.com/rss",
        "https://example.com/atom",
    )

    with caplog.at_level(logging.WARNING):
        articles = fetch_articles([theme], NOW, _parse)

    assert len(articles) == 2
    assert "src-0" in caplog.text
