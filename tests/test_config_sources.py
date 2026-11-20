from pathlib import Path

import pytest

from veille.config import load_sources


def _write(tmp_path: Path, content: str) -> Path:
    path = tmp_path / "sources.yml"
    path.write_text(content, encoding="utf-8")
    return path


def test_sources_yml_du_projet_est_valide() -> None:
    themes = load_sources()

    assert {t.key for t in themes} == {"ia", "automatisation-ia", "dbt", "python"}
    assert all(t.feeds and t.keywords for t in themes)


def test_load_sources_construit_les_dataclasses(tmp_path: Path) -> None:
    path = _write(
        tmp_path,
        "themes:\n"
        "  dbt:\n"
        "    label: dbt\n"
        "    keywords: [DBT, SQL]\n"
        "    feeds:\n"
        "      - {name: Blog, url: 'https://example.com/rss'}\n",
    )

    (theme,) = load_sources(path)

    assert theme.label == "dbt"
    assert theme.keywords == ("dbt", "sql")
    assert theme.feeds[0].url == "https://example.com/rss"


def test_load_sources_sans_themes_leve_une_erreur(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="themes"):
        load_sources(_write(tmp_path, "autre: 1\n"))


def test_load_sources_theme_sans_flux_leve_une_erreur(tmp_path: Path) -> None:
    path = _write(tmp_path, "themes:\n  dbt:\n    label: dbt\n    keywords: [dbt]\n")

    with pytest.raises(ValueError, match="dbt"):
        load_sources(path)


def test_load_sources_flux_sans_url_leve_une_erreur(tmp_path: Path) -> None:
    path = _write(
        tmp_path,
        "themes:\n"
        "  dbt:\n"
        "    label: dbt\n"
        "    keywords: [dbt]\n"
        "    feeds:\n"
        "      - {name: Blog}\n",
    )

    with pytest.raises(ValueError, match="url"):
        load_sources(path)
