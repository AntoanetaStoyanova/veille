import json
import subprocess
from typing import Any

import pytest

from veille.bin import llm
from veille.bin.llm import ask_json


def _envelope(result: str, is_error: bool = False) -> str:
    return json.dumps({"type": "result", "is_error": is_error, "result": result})


def _fake_run(
    monkeypatch: pytest.MonkeyPatch,
    stdout: str = "",
    returncode: int = 0,
    stderr: str = "boom",
) -> list[dict[str, Any]]:
    calls: list[dict[str, Any]] = []

    def run(cmd: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
        calls.append({"cmd": cmd, **kwargs})
        return subprocess.CompletedProcess(cmd, returncode, stdout, stderr)

    monkeypatch.setattr(llm.subprocess, "run", run)
    return calls


def test_ask_json_renvoie_l_objet_de_la_reponse(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _fake_run(monkeypatch, _envelope('{"a": 1}'))

    assert ask_json("modele-x", "prompt") == {"a": 1}


def test_ask_json_envoie_le_prompt_sur_stdin_sans_outil(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = _fake_run(monkeypatch, _envelope("{}"))

    ask_json("modele-x", "mon prompt")

    cmd = calls[0]["cmd"]
    assert calls[0]["input"] == "mon prompt"
    assert cmd[cmd.index("--model") + 1] == "modele-x"
    assert cmd[cmd.index("--tools") + 1] == ""


def test_ask_json_reponse_non_json_leve_une_erreur(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _fake_run(monkeypatch, _envelope("voici mes notes : 4"))

    with pytest.raises(ValueError, match="non JSON"):
        ask_json("m", "p")


def test_ask_json_reponse_non_objet_leve_une_erreur(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _fake_run(monkeypatch, _envelope("[4]"))

    with pytest.raises(ValueError, match="inattendue"):
        ask_json("m", "p")


def test_ask_json_code_de_retour_non_nul_leve_une_erreur(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _fake_run(monkeypatch, "", returncode=1)

    with pytest.raises(RuntimeError, match="boom"):
        ask_json("m", "p")


def test_ask_json_erreur_signalee_par_la_cli_leve_une_erreur(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _fake_run(monkeypatch, _envelope("Limite atteinte", is_error=True))

    with pytest.raises(RuntimeError, match="Limite atteinte"):
        ask_json("m", "p")


def test_ask_json_sortie_de_la_cli_illisible_leve_une_erreur(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _fake_run(monkeypatch, "pas du json")

    with pytest.raises(RuntimeError, match="inattendue"):
        ask_json("m", "p")


@pytest.mark.parametrize(
    ("error", "message"),
    [
        (FileNotFoundError(), "introuvable"),
        (subprocess.TimeoutExpired("claude", 1), "sans réponse"),
    ],
)
def test_ask_json_cli_absente_ou_trop_lente_leve_une_erreur(
    monkeypatch: pytest.MonkeyPatch, error: Exception, message: str
) -> None:
    def run(*_: Any, **__: Any) -> None:
        raise error

    monkeypatch.setattr(llm.subprocess, "run", run)

    with pytest.raises(RuntimeError, match=message):
        ask_json("m", "p")


def test_ask_json_echec_affiche_le_resultat_de_l_enveloppe(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _fake_run(
        monkeypatch, _envelope("Not logged in", is_error=True), returncode=1, stderr=""
    )

    with pytest.raises(RuntimeError, match="Not logged in"):
        ask_json("m", "p")
