"""Appel de Claude via la CLI `claude -p` avec réponse JSON."""

import json
import subprocess
from collections.abc import Callable
from typing import Any

LLM = Callable[[str, str], dict[str, Any]]

TIMEOUT_S = 600


def ask_json(model: str, prompt: str) -> dict[str, Any]:
    """
    Envoie un prompt à la CLI Claude et décode la réponse comme un objet JSON.

    Aucun outil n'est activé : le prompt contient du texte externe non fiable.

    Parameters
    ----------
    model : str
        Identifiant du modèle.
    prompt : str
        Message utilisateur, transmis sur l'entrée standard.

    Returns
    -------
    dict[str, Any]
        Objet JSON de la réponse.

    Raises
    ------
    RuntimeError
        Si la CLI est absente, échoue ou dépasse le délai.
    ValueError
        Si la réponse n'est pas un objet JSON.
    """
    cmd = ["claude", "-p", "--model", model, "--output-format", "json", "--tools", ""]
    try:
        proc = subprocess.run(
            cmd, input=prompt, capture_output=True, text=True, timeout=TIMEOUT_S
        )
    except FileNotFoundError as exc:
        raise RuntimeError("CLI `claude` introuvable") from exc
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError(f"CLI `claude` sans réponse après {TIMEOUT_S} s") from exc
    if proc.returncode != 0:
        raise RuntimeError(f"CLI `claude` en échec : {proc.stderr[:200]!r}")

    try:
        envelope = json.loads(proc.stdout)
        if envelope["is_error"]:
            raise RuntimeError(f"CLI `claude` en erreur : {envelope['result'][:200]!r}")
        text = envelope["result"]
    except (json.JSONDecodeError, KeyError, TypeError) as exc:
        raise RuntimeError(
            f"Sortie inattendue de la CLI : {proc.stdout[:200]!r}"
        ) from exc

    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Réponse non JSON : {text[:200]!r}") from exc
    if not isinstance(data, dict):
        raise ValueError(f"Réponse JSON inattendue (objet attendu) : {text[:200]!r}")
    return data
