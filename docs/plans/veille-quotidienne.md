---
type: plan
statut: en cours
redige_le: 2026-11-20
---

# Plan — Veille quotidienne par mail

*Rédigé le : 20 novembre 2026*
*Référence : [veille-quotidienne.md](../specs/veille-quotidienne.md)*

## Objectif

Pipeline Python complet (collecte → filtre → tri LLM → résumé → mail) déclenché par cron-job.org via `workflow_dispatch`, historique commité sur `main`.

## Prérequis

- Clé API Anthropic, adresse Gmail avec mot de passe d'application (validation en 2 étapes activée), à ajouter en secrets du dépôt avant l'étape 8.
- Dépôt GitHub `AntoanetaStoyanova/veille` accessible, compte cron-job.org.

## Étape 1 — Fondations

- [x] `uv add beartype feedparser anthropic pyyaml` et `uv add --dev types-PyYAML`.
- [x] `src/veille/__init__.py` : appeler `beartype_this_package()`, exposer `main` (importé depuis `veille.bin.pipeline`) ; `__main__.py` réduit à `from . import main; main()`.
- [x] `.gitignore` : ajouter `logs/`.
- [x] `src/veille/log/__init__.py` : ne pas rajouter de handlers si le logger en a déjà ; corriger la ligne `def` > 88 caractères.
- [x] `src/veille/config/` : `sources.yml` (sources par thème : IA, automatisation IA, dbt, Python, mots-clés), `settings.py` (constantes : modèles, fenêtre 3 jours, plafond 40 candidats, 8 items, 90 jours de purge), `load_sources()` → dataclasses typées.
- [x] Tests : chargement de `sources.yml` valide, erreur claire si thème ou URL manquant ; `setup_logging` appelé deux fois n'ajoute pas de doublons.

## Étape 2 — Collecte

- [x] `src/veille/bin/collect.py` : dataclass `Article` (titre, url, source, thème, date, extrait) ; `fetch_articles(sources)` parse chaque flux avec `feedparser`, ignore un flux en erreur (log d'avertissement), filtre sur la fenêtre de fraîcheur.
- [x] Tests : parsing d'un flux RSS et d'un Atom fournis en chaînes (sans réseau), article hors fenêtre exclu, flux cassé ignoré sans interrompre les autres.

## Étape 3 — Historique et pré-filtre

- [x] `src/veille/data/seen.py` : `load_seen(path)`, `save_seen(path, seen)` (écriture atomique), `prune(seen, today)` (90 jours).
- [x] `src/veille/bin/prefilter.py` : `drop_seen()`, dédoublonnage par URL normalisée au sein du lot, `keyword_filter()` par thème, plafond de 40 candidats (les plus récents).
- [x] Tests : fichier absent → historique vide, URL déjà vue exclue, doublon intra-lot supprimé, purge à 90 jours, plafond respecté.

## Étape 4 — Notation LLM

- [x] `src/veille/bin/scoring.py` : `score_articles(articles, client)` envoie un lot unique à Haiku avec le profil d'intérêts, attend un JSON `{url: note}` ; `select_top(scored, n=8)` choisit les meilleurs et désigne l'item « à la une ».
- [x] Gestion d'une réponse JSON invalide : une erreur explicite (pas de repli silencieux).
- [x] Tests : client Anthropic factice, parsing de la réponse, JSON invalide → erreur, tri et sélection, « à la une » = meilleure note.

## Étape 5 — Résumé

- [x] `src/veille/bin/summarize.py` : `summarize(articles, client)` appelle Sonnet, produit pour chaque item les blocs « Ce qui se passe », « Pourquoi c'est important », « Expliqué simplement » (≈ 100 mots, français, termes techniques anglais entre parenthèses) ; dataclass `Digest`.
- [x] Tests : client factice, structure de sortie complète pour chaque item, item manquant dans la réponse → erreur.

## Étape 6 — Mail

- [x] `src/veille/bin/mail.py` : `render(digest, date)` → (sujet `Veille du JJ/MM — N items`, HTML, texte brut) avec « À la une » puis sections thématiques, sections vides omises ; `send(subject, html, text, settings)` via `smtplib.SMTP_SSL` (secrets lus dans l'environnement).
- [x] Tests : sujet et nombre d'items, section vide omise, échappement HTML du contenu, `send` avec `smtplib` mocké, variable d'environnement manquante → erreur claire.

## Étape 7 — Orchestration et CLI

- [x] `src/veille/bin/pipeline.py` : `run(dry_run: bool)` enchaîne collecte → filtre → tri → résumé → rendu ; envoie puis met à jour `seen.json` (jamais avant l'envoi) ; si aucun article, ne pas envoyer de mail vide (log).
- [x] `main()` : option `--dry-run` (affiche le mail, aucun envoi, aucune écriture).
- [x] `tasks/__init__.py` : tâche `run` (`uv run python -m veille`) et `dry_run`.
- [x] Tests : pipeline complet avec toutes les dépendances factices, échec d'envoi → `seen.json` inchangé, `--dry-run` n'écrit rien, zéro article → pas de mail.

## Étape 8 — Workflow, cron et documentation

- [ ] `.github/workflows/veille.yml` : déclencheur `workflow_dispatch` seul, `permissions: contents: write`, groupe de concurrence, `astral-sh/setup-uv`, `uv sync`, exécution du pipeline avec les secrets, commit de `seen.json` seulement s'il a changé, step `if: failure()` qui envoie un mail d'erreur court.
- [ ] README : variables d'environnement, création du mot de passe d'application Gmail, des secrets GitHub, du PAT fine-grained (dépôt unique, *Actions: Read and write*, expiration, rappel de renouvellement) et du job cron-job.org (`POST .../actions/workflows/veille.yml/dispatches`, body `{"ref":"main"}`, attente HTTP 204, notification d'échec activée).
- [ ] Merge `develop` → `main` (action manuelle d'Antoaneta), puis déclenchement manuel du workflow pour validation.
- [ ] Tests : validité YAML du workflow (chargement `yaml.safe_load`, présence de `workflow_dispatch` et absence de `schedule`).

## Critères de fin

- [ ] `uv run inv ci` passe
- [ ] `uv run python -m veille --dry-run` affiche un mail en français avec ≤ 8 items, groupés par section
- [ ] Un article déjà envoyé ne revient jamais ; section vide omise
- [ ] Échec d'envoi : `seen.json` inchangé
- [ ] Workflow exécuté sur `main` : mail reçu, `seen.json` commité seulement s'il a changé
- [ ] Un échec du workflow envoie un mail d'erreur court
- [ ] Aucun secret dans le code, les logs ou le dépôt
