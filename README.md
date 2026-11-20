# veille

Un pipeline Python déclenché chaque matin via cron-job.org et GitHub Actions, qui collecte des articles sur l'IA, dbt et Python, les résume et les explique en français avec Claude, puis les envoie dans un seul mail.

## Auteur

Antoaneta Stoyanova

## Prérequis

- Python >= 3.13
- [uv](https://docs.astral.sh/uv/)
- [cruft](https://cruft.github.io/cruft/) — pour mettre à jour le template

## Installation

```bash
git clone git@github.com:AntoanetaStoyanova/veille.git
cd veille
uv sync
```

## Utilisation

```bash
uv run python -m veille
```

## Mettre à jour depuis le template

```bash
cruft update
```
