---
type: spec
statut: en cours
redige_le: 2026-11-20
---

# Spec — Veille quotidienne par mail

*Rédigé le : 20 novembre 2026*

## Contexte

Antoaneta veut une veille quotidienne centrée sur ses sujets : nouveautés IA, automatisation IA, dbt, Python. Les sources sont majoritairement en anglais ; elle veut des explications détaillées mais courtes, en français. Le projet `veille` est un squelette issu du template cruft, sans logique métier.

## Objectif

Chaque matin, un seul mail en français : un item « à la une » puis des sections thématiques, 8 items maximum, lisible en 5 à 7 minutes. Le déclenchement vient de cron-job.org via `workflow_dispatch` de GitHub Actions.

## Périmètre

- Collecte RSS/Atom (blogs, arXiv, Hacker News, releases GitHub) listée dans `config/sources.yml`.
- Fenêtre de fraîcheur, dédoublonnage via `seen.json`, pré-filtre par mots-clés par thème.
- Notation de pertinence (1-5) par Claude Haiku, sélection des 8 meilleurs.
- Résumé détaillé en français par Claude (Sonnet), format fixe par item.
- Mail HTML + texte brut envoyé via Gmail SMTP, sections vides omises.
- Workflow GitHub Actions `workflow_dispatch` qui exécute le pipeline, commite `seen.json` sur `main`, envoie un mail d'erreur en cas d'échec.
- Option `--dry-run` : affiche le mail sans l'envoyer ni modifier l'historique.

## Hors périmètre

- Feedback 👍/👎 et apprentissage du profil.
- Archive consultable, base de données, recherche.
- Sources sans flux RSS/Atom (scraping HTML).
- Planification par le `schedule:` natif de GitHub.
- Création et configuration du job cron-job.org (action manuelle, documentée).

## Décisions

| Sujet | Décision | Raison |
|-------|----------|--------|
| Déclenchement | `workflow_dispatch` seul, appelé par cron-job.org (fuseau Europe/Paris) | `schedule:` GitHub peu fiable (retards, désactivation après 60 j d'inactivité) |
| Historique | `src/veille/data/seen.json` commité sur `main` par le workflow | Simple et versionné ; le contenu (URLs publiques) n'est pas sensible |
| Format de l'historique | `{url: date_envoi}`, purge des entrées de plus de 90 jours | Borne la taille du fichier |
| Marquage « vu » | Seulement après envoi réussi du mail | Un échec d'envoi ne doit pas perdre d'articles |
| Fraîcheur | Articles publiés depuis moins de 3 jours | Évite le déluge au premier lancement |
| Tri | Mots-clés par thème, puis Haiku note 1-5 (plafond de 40 candidats) | Qualité sans payer pour du bruit |
| Résumé | Sonnet, 4 blocs : Ce qui se passe / Pourquoi c'est important / Expliqué simplement / Lien, ~100 mots | Besoin d'explications détaillées mais courtes |
| Langue | Mail toujours en français, termes techniques anglais entre parenthèses | Un résumé français d'une source anglaise est plus utile |
| Modèles | Constantes dans `config/` (`claude-haiku-5-5` tri, `claude-sonnet-5-5` résumé) | Changement de modèle sans toucher à la logique |
| Mail | `smtplib` + mot de passe d'application Gmail | Aucune dépendance ni compte en plus |
| Secrets | `ANTHROPIC_API_KEY`, `GMAIL_ADDRESS`, `GMAIL_APP_PASSWORD`, `MAIL_TO` en secrets du dépôt | Jamais dans le code |
| Organisation du code | Modules métier dans `bin/`, `main()` exposé par `__init__.py`, `__main__.py` minimal | `CONTRIBUTING.md` du projet |
| Typage runtime | `beartype_this_package()` dans `__init__.py`, `uv add beartype` | Standards globaux |
| Branche cible | Le workflow et le cron visent `main` ; merge `develop` → `main` avant mise en production | `workflow_dispatch` via API exige le workflow sur le `ref` ciblé |
| Tests | Réseau, API Claude et SMTP toujours mockés | Seuil de couverture 88 % bloquant |

## Critères d'acceptation

- [ ] `uv run python -m veille --dry-run` affiche un mail en français avec ≤ 8 items, groupés par section, sans envoyer ni écrire `seen.json`.
- [ ] Un article déjà présent dans `seen.json` n'apparaît jamais dans un nouveau mail.
- [ ] Une section sans item n'apparaît pas dans le mail.
- [ ] Si l'envoi du mail échoue, `seen.json` n'est pas modifié.
- [ ] Le workflow `workflow_dispatch` s'exécute sur `main`, envoie le mail et commite `seen.json` seulement s'il a changé.
- [ ] Un échec du workflow envoie un mail d'erreur court.
- [ ] Aucun secret n'apparaît dans le code, les logs ou le dépôt.
- [ ] `uv run inv ci` passe, couverture ≥ 88 %.
