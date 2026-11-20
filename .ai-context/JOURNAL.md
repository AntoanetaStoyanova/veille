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
- Plan llm-abonnement-claude (`docs/specs/llm-abonnement-claude.md`, `docs/plans/llm-abonnement-claude.md`, 3 étapes) créés : remplacer le client `anthropic` (clé API payante) par `claude -p` + token OAuth de l'abonnement. Décisions : injection d'un appelable `llm(modèle, prompt)`, aucun outil exposé à la CLI (texte RSS non fiable), `anthropic` retirée.
- Plan llm-abonnement-claude — Étape 1 : Appel CLI et injection de `llm` (`bin/llm.py` : `LLM`, `ask_json(model, prompt)` via `claude -p --output-format json --tools ""`, prompt sur stdin, délai 600 s ; `scoring.py`, `summarize.py`, `pipeline.py` : `llm` à la place de `client` ; `anthropic` retirée de `pyproject.toml` et `uv.lock` ; `tests/helpers.py` : `make_llm` ; `tests/test_llm.py`). CLI absente, échec, `is_error` ou délai → `RuntimeError` ; réponse non JSON → `ValueError`. Format de sortie vérifié sur la CLI réelle (champs `is_error` et `result`).
- Plan veille-quotidienne — Étape 8 (partielle) : `.github/workflows/veille.yml`, section « Mise en production » du `README.md`, `send_failure` dans `bin/mail.py` (mail d'erreur appelé par le step `if: failure()`), `tests/test_workflow.py`. Le workflow n'a pas pu être exécuté ici : il reste à valider sur GitHub.
- Plan llm-abonnement-claude — Étape 2 : Workflow et documentation (`.github/workflows/veille.yml` : secret `CLAUDE_CODE_OAUTH_TOKEN` + step `npm install -g @anthropic-ai/claude-code` avant la veille ; `tests/test_workflow.py` : variables attendues + ordre d'installation ; `README.md` : variable, prérequis local, secrets).

### Reste à faire

- Exécuter `docs/plans/llm-abonnement-claude.md` — Étape 3 : validation réelle (manuelle) : `inv dry-run`, release, merge sur `main`, déclenchement du workflow.
- Exécuter `docs/plans/veille-quotidienne.md` — Étape 8 : tâche manuelle restante, merge `develop` → `main` (Antoaneta), puis déclenchement manuel du workflow pour validation.
- Avant le déclenchement : vérifier les 4 secrets du dépôt (`CLAUDE_CODE_OAUTH_TOKEN`, `GMAIL_ADDRESS`, `GMAIL_APP_PASSWORD`, `MAIL_TO`) et le PAT fine-grained (voir README).
- Ensuite : cocher les « Critères de fin » du plan et de la spec, passer leur `statut` à `fait`.

### Références

- [Spec](../docs/specs/veille-quotidienne.md)
- [Plan](../docs/plans/veille-quotidienne.md)
- [Spec LLM](../docs/specs/llm-abonnement-claude.md)
- [Plan LLM](../docs/plans/llm-abonnement-claude.md)
- `src/veille/config/`, `src/veille/log/__init__.py`, `src/veille/bin/collect.py`, `src/veille/bin/prefilter.py`, `src/veille/bin/scoring.py`, `src/veille/bin/summarize.py`, `src/veille/bin/mail.py`, `src/veille/bin/llm.py`, `src/veille/bin/pipeline.py`, `tests/test_pipeline.py`, `src/veille/data/seen.py`, `tests/test_config_sources.py`, `tests/test_log_setup.py`, `tests/test_collect.py`, `.github/workflows/veille.yml`, `tests/test_workflow.py`, `README.md`
