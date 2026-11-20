import json
import logging
from datetime import UTC, date, datetime
from email.utils import format_datetime
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import anthropic
import feedparser
import pytest

from tests.helpers import make_message
from veille.bin import pipeline
from veille.bin.pipeline import main, run
from veille.config.settings import MODEL_SCORING
from veille.data.seen import load_seen, save_seen

TODAY = date(2026, 11, 20)
URLS = ("https://news.example/1", "https://news.example/2")
SCORES = {URLS[0]: 5, URLS[1]: 3}
SUMMARIES = {
    url: {
        "ce_qui_se_passe": f"faits {n}",
        "pourquoi_important": f"impact {n}",
        "explique_simplement": f"image {n}",
    }
    for n, url in enumerate(URLS, start=1)
}


def _parse(url: str) -> Any:
    pub = format_datetime(datetime.now(UTC))
    items = "".join(
        f"<item><title>LLM agent {n}</title><link>{u}</link>"
        f"<description>texte</description><pubDate>{pub}</pubDate></item>"
        for n, u in enumerate(URLS, start=1)
    )
    return feedparser.parse(f'<rss version="2.0"><channel>{items}</channel></rss>')


def _parse_empty(url: str) -> Any:
    return feedparser.parse('<rss version="2.0"><channel></channel></rss>')


def _client() -> MagicMock:
    def create(*, model: str, **_: Any) -> Any:
        return make_message(json.dumps(SCORES if model == MODEL_SCORING else SUMMARIES))

    client = MagicMock(spec=anthropic.Anthropic)
    client.messages.create.side_effect = create
    return client


@pytest.fixture
def mail_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GMAIL_ADDRESS", "moi@gmail.com")
    monkeypatch.setenv("GMAIL_APP_PASSWORD", "secret-app")
    monkeypatch.setenv("MAIL_TO", "elle@example.com")


def _run(seen_path: Path, mailer: MagicMock, **kwargs: Any) -> None:
    run(
        client=kwargs.pop("client", _client()),
        parse=kwargs.pop("parse", _parse),
        mailer=mailer,
        seen_path=seen_path,
        today=TODAY,
        **kwargs,
    )


@pytest.mark.usefixtures("mail_env")
def test_run_envoie_le_mail_puis_met_a_jour_l_historique(tmp_path: Path) -> None:
    seen_path, mailer = tmp_path / "seen.json", MagicMock()

    _run(seen_path, mailer)

    mailer.assert_called_once()
    subject, html, text, settings = mailer.call_args.args
    assert subject == "Veille du 20/11 — 2 items"
    assert "faits 1" in text and "faits 1" in html
    assert settings.to == "elle@example.com"
    assert load_seen(seen_path) == dict.fromkeys(URLS, TODAY)


@pytest.mark.usefixtures("mail_env")
def test_run_echec_d_envoi_laisse_seen_inchange(tmp_path: Path) -> None:
    seen_path = tmp_path / "seen.json"
    save_seen(seen_path, {"https://old.example/x": TODAY})
    before = seen_path.read_text(encoding="utf-8")
    mailer = MagicMock(side_effect=OSError("SMTP indisponible"))

    with pytest.raises(OSError):
        _run(seen_path, mailer)

    assert seen_path.read_text(encoding="utf-8") == before


@pytest.mark.usefixtures("mail_env")
def test_run_n_envoie_pas_deux_fois_le_meme_article(tmp_path: Path) -> None:
    seen_path, mailer = tmp_path / "seen.json", MagicMock()

    _run(seen_path, mailer)
    _run(seen_path, mailer)

    mailer.assert_called_once()


def test_run_dry_run_affiche_le_mail_sans_rien_envoyer_ni_ecrire(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    seen_path, mailer = tmp_path / "seen.json", MagicMock()

    with caplog.at_level(logging.INFO, logger=pipeline.logger.name):
        _run(seen_path, mailer, dry_run=True)

    mailer.assert_not_called()
    assert not seen_path.exists()
    assert "Veille du 20/11" in caplog.text


@pytest.mark.usefixtures("mail_env")
def test_run_sans_article_n_envoie_pas_de_mail(tmp_path: Path) -> None:
    seen_path, mailer, client = tmp_path / "seen.json", MagicMock(), _client()

    _run(seen_path, mailer, parse=_parse_empty, client=client)

    mailer.assert_not_called()
    client.messages.create.assert_not_called()
    assert not seen_path.exists()


def test_run_variable_mail_manquante_echoue_avant_les_appels_claude(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("GMAIL_ADDRESS", raising=False)
    client = _client()

    with pytest.raises(ValueError, match="GMAIL_ADDRESS"):
        _run(tmp_path / "seen.json", MagicMock(), client=client)

    client.messages.create.assert_not_called()


@pytest.mark.parametrize(("argv", "expected"), [(["--dry-run"], True), ([], False)])
def test_main_transmet_l_option_dry_run(
    argv: list[str],
    expected: bool,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake_run = MagicMock()
    monkeypatch.setattr(pipeline, "run", fake_run)
    monkeypatch.chdir(tmp_path)

    main(argv)

    fake_run.assert_called_once_with(dry_run=expected)
