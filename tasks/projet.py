"""Tâches propres au projet — non écrasées par `cruft update` (voir `skip`)."""

from invoke import Context, task


@task
def run(c: Context) -> None:
    """Lance la veille : envoie le mail et met à jour l'historique."""
    c.run("uv run python -m veille")


@task
def dry_run(c: Context) -> None:
    """Affiche le mail du jour sans l'envoyer ni modifier l'historique."""
    c.run("uv run python -m veille --dry-run")
