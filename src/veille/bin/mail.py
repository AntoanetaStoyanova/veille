"""Rendu et envoi du mail de veille."""

import os
import smtplib
import ssl
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import date
from email.message import EmailMessage
from html import escape

from veille.bin.summarize import Digest, DigestItem
from veille.config import Theme
from veille.config.settings import SMTP_HOST, SMTP_PORT

HEADLINE_LABEL = "À la une"
ENV_VARS = ("GMAIL_ADDRESS", "GMAIL_APP_PASSWORD", "MAIL_TO")


@dataclass(frozen=True)
class MailSettings:
    """
    Identifiants et destinataire du mail.

    Attributes
    ----------
    address : str
        Adresse Gmail d'envoi.
    password : str
        Mot de passe d'application Gmail.
    to : str
        Adresse du destinataire.
    """

    address: str
    password: str
    to: str


def load_mail_settings(env: Mapping[str, str] = os.environ) -> MailSettings:
    """
    Lit les identifiants du mail dans l'environnement.

    Parameters
    ----------
    env : Mapping[str, str]
        Variables d'environnement.

    Returns
    -------
    MailSettings
        Identifiants et destinataire.

    Raises
    ------
    ValueError
        Si `GMAIL_ADDRESS`, `GMAIL_APP_PASSWORD` ou `MAIL_TO` manque ou est vide.
    """
    missing = [name for name in ENV_VARS if not env.get(name)]
    if missing:
        raise ValueError(f"Variables d'environnement manquantes : {', '.join(missing)}")
    return MailSettings(
        address=env["GMAIL_ADDRESS"],
        password=env["GMAIL_APP_PASSWORD"],
        to=env["MAIL_TO"],
    )


def _blocks(item: DigestItem) -> list[tuple[str, str]]:
    """Blocs (titre, texte) d'un item, dans l'ordre d'affichage."""
    return [
        ("Ce qui se passe", item.what_happens),
        ("Pourquoi c'est important", item.why_important),
        ("Expliqué simplement", item.explained_simply),
    ]


def _sections(
    digest: Digest, themes: Sequence[Theme]
) -> list[tuple[str, list[DigestItem]]]:
    """« À la une » puis une section par thème non vide, dans l'ordre des thèmes."""
    sections = [(HEADLINE_LABEL, [digest.headline])]
    for theme in themes:
        items = [i for i in digest.others if i.article.theme == theme.key]
        if items:
            sections.append((theme.label, items))
    return sections


def _item_html(item: DigestItem) -> str:
    """Bloc HTML d'un item, contenu échappé."""
    a = item.article
    blocks = "".join(
        f"<p><strong>{escape(label)}</strong><br>{escape(text)}</p>"
        for label, text in _blocks(item)
    )
    return (
        f'<h3><a href="{escape(a.url)}">{escape(a.title)}</a></h3>'
        f'<p style="color:#666">{escape(a.source)}</p>{blocks}'
    )


def _item_text(item: DigestItem) -> str:
    """Bloc texte brut d'un item."""
    a = item.article
    blocks = "\n".join(f"{label} : {text}" for label, text in _blocks(item))
    return f"{a.title} ({a.source})\n{blocks}\nLien : {a.url}"


def render(digest: Digest, themes: Sequence[Theme], day: date) -> tuple[str, str, str]:
    """
    Compose le sujet, la version HTML et la version texte du mail.

    Parameters
    ----------
    digest : Digest
        Items du jour.
    themes : Sequence[Theme]
        Thèmes, pour l'ordre et le titre des sections.
    day : date
        Jour de la veille.

    Returns
    -------
    tuple[str, str, str]
        Sujet, HTML, texte brut. Les sections sans item sont omises.
    """
    sections = _sections(digest, themes)
    count = sum(len(items) for _, items in sections)
    subject = f"Veille du {day:%d/%m} — {count} item{'s' if count > 1 else ''}"

    html_parts = [f"<h1>{escape(subject)}</h1>"]
    text_parts = [subject]
    for label, items in sections:
        html_parts.append(f"<h2>{escape(label)}</h2>")
        html_parts.extend(_item_html(i) for i in items)
        text_parts.append(f"{label.upper()}\n{'=' * len(label)}")
        text_parts.extend(_item_text(i) for i in items)

    body = "".join(html_parts)
    html = (
        '<html><body style="font-family:sans-serif;max-width:640px">'
        f"{body}</body></html>"
    )
    return subject, html, "\n\n".join(text_parts) + "\n"


def send(subject: str, html: str, text: str, settings: MailSettings) -> None:
    """
    Envoie un mail multipart (texte et HTML) via Gmail SMTP.

    Parameters
    ----------
    subject : str
        Sujet du mail.
    html : str
        Version HTML.
    text : str
        Version texte brut.
    settings : MailSettings
        Identifiants et destinataire.
    """
    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = settings.address
    message["To"] = settings.to
    message.set_content(text)
    message.add_alternative(html, subtype="html")

    context = ssl.create_default_context()
    with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, context=context) as smtp:
        smtp.login(settings.address, settings.password)
        smtp.send_message(message)
