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
uv run inv dry-run   # affiche le mail sans l'envoyer ni modifier l'historique
uv run inv run       # envoie le mail et met à jour l'historique
```

Les sources et les mots-clés se règlent dans `src/veille/config/sources.yml`.

## Variables d'environnement

| Variable | Rôle |
|----------|------|
| `CLAUDE_CODE_OAUTH_TOKEN` | Jeton d'abonnement Claude (tri et résumé), généré avec `claude setup-token` |
| `GMAIL_ADDRESS` | Adresse Gmail d'envoi |
| `GMAIL_APP_PASSWORD` | Mot de passe d'application Gmail |
| `MAIL_TO` | Destinataire du mail |

En local, `dry-run` n'a besoin que de la CLI `claude` connectée à l'abonnement (`claude` puis `/login`) ; pas de clé API.

## Mise en production

Le workflow `.github/workflows/veille.yml` ne se lance que par `workflow_dispatch` sur `main` : il envoie le mail, puis commite `src/veille/data/seen.json` s'il a changé. Un échec envoie un mail d'erreur court.

### 1. Mot de passe d'application Gmail

1. Activer la validation en 2 étapes sur le compte Google.
2. Ouvrir <https://myaccount.google.com/apppasswords>, créer un mot de passe nommé `veille`.
3. Le copier (16 caractères) : il sert de `GMAIL_APP_PASSWORD`.

### 2. Secrets du dépôt

Dépôt GitHub → *Settings* → *Secrets and variables* → *Actions* → *New repository secret* : créer `CLAUDE_CODE_OAUTH_TOKEN` (valeur donnée par `claude setup-token`), `GMAIL_ADDRESS`, `GMAIL_APP_PASSWORD` et `MAIL_TO`.

### 3. Jeton d'accès (PAT) pour cron-job.org

GitHub → *Settings* → *Developer settings* → *Personal access tokens* → *Fine-grained tokens* :

- *Repository access* : uniquement `AntoanetaStoyanova/veille`.
- *Permissions* → *Repository permissions* → *Actions* : **Read and write**.
- *Expiration* : 90 jours maximum ; noter un rappel de renouvellement avant l'échéance, sinon le job échoue.

### 4. Job cron-job.org

Créer un job avec :

- URL : `https://api.github.com/repos/AntoanetaStoyanova/veille/actions/workflows/veille.yml/dispatches`
- Méthode : `POST`, corps : `{"ref":"main"}`
- En-têtes : `Authorization: Bearer <PAT>`, `Accept: application/vnd.github+json`, `Content-Type: application/json`
- Fuseau horaire : `Europe/Paris`, heure d'envoi au choix.
- Réponse attendue : HTTP `204`.
- Notification en cas d'échec : activée.

### 5. Premier lancement

Fusionner `develop` dans `main`, puis lancer le workflow à la main (*Actions* → *veille* → *Run workflow*) et vérifier le mail reçu.

Si `main` est protégée, autoriser `github-actions[bot]` à pousser : le workflow commite l'historique directement dessus.

## Mettre à jour depuis le template

```bash
cruft update
```
