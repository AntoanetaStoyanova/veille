from pathlib import Path
from typing import Any

import yaml

WORKFLOW = Path(__file__).parents[1] / ".github" / "workflows" / "veille.yml"


def _load() -> dict[Any, Any]:
    return yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))  # type: ignore[no-any-return]


def test_workflow_se_declenche_uniquement_par_workflow_dispatch() -> None:
    # PyYAML lit la clé `on` comme le booléen True (YAML 1.1).
    workflow = _load()
    triggers = workflow.get("on", workflow.get(True))

    assert "workflow_dispatch" in triggers
    assert "schedule" not in triggers
    assert set(triggers) == {"workflow_dispatch"}


def test_workflow_peut_ecrire_le_depot_et_ne_se_chevauche_pas() -> None:
    workflow = _load()

    assert workflow["permissions"] == {"contents": "write"}
    assert workflow["concurrency"]["group"]


def test_workflow_envoie_un_mail_d_erreur_en_cas_d_echec() -> None:
    steps = _load()["jobs"]["veille"]["steps"]

    failure_steps = [s for s in steps if s.get("if") == "failure()"]

    assert len(failure_steps) == 1
    assert "send_failure" in failure_steps[0]["run"]


def test_workflow_lit_les_secrets_depuis_les_secrets_du_depot() -> None:
    env = _load()["env"]

    assert set(env) == {
        "ANTHROPIC_API_KEY",
        "GMAIL_ADDRESS",
        "GMAIL_APP_PASSWORD",
        "MAIL_TO",
    }
    assert all(v.startswith("${{ secrets.") for v in env.values())
