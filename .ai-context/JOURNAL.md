# Journal — veille

> **Usage — Claude Code** : ce fichier trace l'avancement du projet session par session —
> ce qui a été fait et ce qu'il reste à faire. Contrairement à `CURRENT.md` (état du code
> au moment d'une review), ce journal suit les décisions, les documents créés et les étapes
> franchies. Ajoute une entrée en haut (sous ce bloc) à chaque session de travail
> significative. Ne supprime pas les entrées précédentes.
>
> Format d'une entrée :
>
> ## [YYYY-MM-DD] — <titre court de la session>
> ### Fait
> ### Reste à faire
> ### Références

---

## [2026-11-20] — Planification et fondations de la veille quotidienne

### Fait

- `docs/specs/veille-quotidienne.md` et `docs/plans/veille-quotidienne.md` créés (8 étapes).
- Décisions actées : historique `seen.json` commité sur `main`, Gmail SMTP, tri mots-clés puis Haiku, résumé Sonnet, déclenchement cron-job.org → `workflow_dispatch`.
- Plan veille-quotidienne — Étape 1 : Fondations (dépendances, `__init__.py` avec beartype, `__main__.py`, `.gitignore`, `log/__init__.py`, `config/{__init__,settings}.py` + `sources.yml`, `bin/pipeline.py` provisoire, tests config et log).
- `pyproject.toml` : `packages.find` corrigé (`where=["src"]`, `include=["veille*"]`) + package-data `sources.yml`, car le paquet s'installait sous le nom `src` ; `cruft update` peut signaler un conflit sur ce bloc.
- URLs des flux de `sources.yml` non vérifiées (pas de réseau en test) : un flux cassé est ignoré à la collecte.
- Plan veille-quotidienne — Étape 2 : Collecte (`bin/collect.py` : `Article`, `fetch_articles(themes, now, parse)` ; `tests/test_collect.py`). Article sans date ou sans lien ignoré ; flux illisible = `bozo` sans entrée.
- Plan veille-quotidienne — Étape 3 : Historique et pré-filtre (`data/seen.py`, `bin/prefilter.py`, `tests/test_seen.py`, `tests/test_prefilter.py`). Les clés de `seen.json` sont des URL normalisées (`normalize_url`) ; le filtre par mots-clés cherche aussi dans le nom de la source (titres de release sans sujet).
- Plan veille-quotidienne — Étape 4 : Notation LLM (`bin/scoring.py` : `ScoredArticle`, `score_articles`, `select_top` ; `INTEREST_PROFILE` dans `config/settings.py` ; `tests/test_scoring.py`). JSON invalide, URL absente ou note hors 1-5 → `ValueError` ; `select_top` renvoie une liste dont le premier élément est l'item « à la une ». Tests : `MagicMock(spec=anthropic.Anthropic)` (beartype refuse un faux client non typé).
- Plan veille-quotidienne — Étape 5 : Résumé (`bin/summarize.py` : `DigestItem`, `Digest(headline, others)`, `summarize(articles, client)` ; `bin/llm.py` : `ask_json` extrait de `scoring.py` ; `tests/helpers.py` : `make_client` partagé ; `tests/test_summarize.py`). `summarize` prend les articles dans l'ordre de `select_top` (le premier est « à la une ») ; item ou bloc absent → `ValueError`.
- Plan veille-quotidienne — Étape 6 : Mail (`bin/mail.py` : `render(digest, themes, day)`, `send`, `MailSettings`, `load_mail_settings(env)` ; `SMTP_HOST`/`SMTP_PORT` dans `config/settings.py` ; `tests/test_mail.py`). Variable manquante → `ValueError` qui nomme les variables ; le texte brut met les titres de section en majuscules.
- Plan veille-quotidienne — Étape 7 : Orchestration et CLI (`bin/pipeline.py` : `run(dry_run, *, client, parse, mailer, seen_path, today)` et `main(argv)` avec `--dry-run` ; `SEEN_PATH` dans `config/settings.py` ; tâches `inv run` / `inv dry-run` ; `tests/test_pipeline.py`). Les secrets du mail sont lus avant les appels Claude ; `seen.json` reçoit les URL normalisées des items envoyés, après l'envoi seulement ; en dry-run le mail est journalisé (pas de `print`), et `setup_logging` écrit tout de même un fichier dans `logs/` (ignoré par git).

### Reste à faire

- Exécuter `docs/plans/veille-quotidienne.md` — Étape 8 : Workflow, cron et documentation.
- Avant l'étape 8 : créer la clé API Anthropic, le mot de passe d'application Gmail et le PAT fine-grained.

### Références

- [Spec](../docs/specs/veille-quotidienne.md)
- [Plan](../docs/plans/veille-quotidienne.md)
- `src/veille/config/`, `src/veille/log/__init__.py`, `src/veille/bin/collect.py`, `src/veille/bin/prefilter.py`, `src/veille/bin/scoring.py`, `src/veille/bin/summarize.py`, `src/veille/bin/mail.py`, `src/veille/bin/llm.py`, `src/veille/bin/pipeline.py`, `tests/test_pipeline.py`, `src/veille/data/seen.py`, `tests/test_config_sources.py`, `tests/test_log_setup.py`, `tests/test_collect.py`
