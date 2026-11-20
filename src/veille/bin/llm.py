"""Appel de Claude avec réponse JSON."""

import json
from typing import Any

import anthropic


def ask_json(
    client: anthropic.Anthropic, model: str, max_tokens: int, prompt: str
) -> dict[str, Any]:
    """
    Envoie un prompt et décode la réponse comme un objet JSON.

    Parameters
    ----------
    client : anthropic.Anthropic
        Client de l'API Anthropic.
    model : str
        Identifiant du modèle.
    max_tokens : int
        Longueur maximale de la réponse.
    prompt : str
        Message utilisateur.

    Returns
    -------
    dict[str, Any]
        Objet JSON de la réponse.

    Raises
    ------
    ValueError
        Si la réponse n'est pas un objet JSON.
    """
    response = client.messages.create(
        model=model,
        max_tokens=max_tokens,
        messages=[{"role": "user", "content": prompt}],
    )
    text = "".join(b.text for b in response.content if b.type == "text")
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Réponse non JSON : {text[:200]!r}") from exc
    if not isinstance(data, dict):
        raise ValueError(f"Réponse JSON inattendue (objet attendu) : {text[:200]!r}")
    return data
