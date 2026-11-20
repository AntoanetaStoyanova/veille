from datetime import UTC, date, datetime
from email.message import EmailMessage
from unittest.mock import MagicMock

import pytest

from veille.bin import mail
from veille.bin.collect import Article
from veille.bin.mail import MailSettings, load_mail_settings, render, send
from veille.bin.summarize import Digest, DigestItem
from veille.config import Feed, Theme

THEMES = (
    Theme("ia", "IA", ("ia",), (Feed("Blog", "https://b.com"),)),
    Theme("dbt", "dbt", ("dbt",), (Feed("Blog", "https://d.com"),)),
    Theme("python", "Python", ("python",), (Feed("Blog", "https://p.com"),)),
)
SETTINGS = MailSettings("moi@gmail.com", "secret-app", "elle@example.com")


def _item(n: int, theme: str = "ia", title: str = "", url: str = "") -> DigestItem:
    article = Article(
        title=title or f"Titre {n}",
        url=url or f"https://a.com/{n}",
        source="Blog",
        theme=theme,
        published=datetime(2026, 11, 20, tzinfo=UTC),
        excerpt="",
    )
    return DigestItem(article, f"faits {n}", f"impact {n}", f"image {n}")


def _digest() -> Digest:
    return Digest(
        headline=_item(1, "ia"),
        others=(_item(2, "python"), _item(3, "ia")),
    )


def test_render_donne_le_sujet_avec_la_date_et_le_nombre_d_items() -> None:
    subject, _, _ = render(_digest(), THEMES, date(2026, 11, 20))

    assert subject == "Veille du 20/11 — 3 items"


def test_render_met_a_la_une_en_premier_puis_les_themes_dans_l_ordre() -> None:
    _, html, text = render(_digest(), THEMES, date(2026, 11, 20))

    for body, titles in (
        (html, ("<h2>À la une", "<h2>IA", "<h2>Python")),
        (text, ("À LA UNE", "\nIA\n", "PYTHON")),
    ):
        positions = [body.index(t) for t in titles]
        assert positions == sorted(positions)
        assert body.count("Titre 1") == 1
    assert "faits 2" in text and "Lien : https://a.com/3" in text


def test_render_omet_une_section_vide() -> None:
    _, html, text = render(_digest(), THEMES, date(2026, 11, 20))

    assert "dbt" not in html
    assert "dbt" not in text.lower()


def test_render_echappe_le_html_du_contenu() -> None:
    digest = Digest(
        headline=_item(
            1, title="<script>alert(1)</script> & co", url='https://a.com/?a="1"&b=2'
        ),
        others=(),
    )

    _, html, _ = render(digest, THEMES, date(2026, 11, 20))

    assert "<script>" not in html
    assert "&lt;script&gt;alert(1)&lt;/script&gt; &amp; co" in html
    assert 'href="https://a.com/?a=&quot;1&quot;&amp;b=2"' in html


def test_send_se_connecte_et_envoie_un_mail_texte_et_html(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    smtp_class = MagicMock()
    smtp = smtp_class.return_value.__enter__.return_value
    monkeypatch.setattr(mail.smtplib, "SMTP_SSL", smtp_class)

    send("Sujet", "<p>html</p>", "texte", SETTINGS)

    smtp.login.assert_called_once_with("moi@gmail.com", "secret-app")
    (message,) = smtp.send_message.call_args.args
    assert isinstance(message, EmailMessage)
    assert (message["Subject"], message["From"], message["To"]) == (
        "Sujet",
        "moi@gmail.com",
        "elle@example.com",
    )
    assert message.get_body(("plain",)).get_content().strip() == "texte"
    assert "<p>html</p>" in message.get_body(("html",)).get_content()


def test_send_failure_envoie_le_lien_de_l_execution(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake_send = MagicMock()
    monkeypatch.setattr(mail, "send", fake_send)

    mail.send_failure("https://github.com/x/y/actions/runs/1?a=1&b=2", SETTINGS)

    subject, html, text, settings = fake_send.call_args.args
    assert "échec" in subject
    assert "Logs : https://github.com/x/y/actions/runs/1?a=1&b=2" in text
    assert 'href="https://github.com/x/y/actions/runs/1?a=1&amp;b=2"' in html
    assert settings is SETTINGS


def test_load_mail_settings_lit_les_trois_variables() -> None:
    env = {
        "GMAIL_ADDRESS": "moi@gmail.com",
        "GMAIL_APP_PASSWORD": "secret-app",
        "MAIL_TO": "elle@example.com",
    }

    assert load_mail_settings(env) == SETTINGS


def test_load_mail_settings_variable_manquante_nomme_la_variable() -> None:
    env = {"GMAIL_ADDRESS": "moi@gmail.com", "MAIL_TO": ""}

    with pytest.raises(ValueError, match="GMAIL_APP_PASSWORD, MAIL_TO"):
        load_mail_settings(env)
