# Guetteur

Guetteur surveille les événements de sécurité d'un site que son propriétaire a autorisé. La V1a vise la collecte par SDK, huit règles de détection, des alertes email, un tableau de bord et un journal d'audit. La V1b et les versions ultérieures restent hors périmètre.

Le cadrage et les fondations locales sont présents. Le service API actuel expose uniquement un contrôle de santé; l'authentification, l'ingestion, les règles et l'interface ne sont pas encore implémentées. Rien n'est déployé.

## Démarrage local

Prérequis : Docker avec Compose, Python 3.12 ou plus récent et Git.

La liste des variables et les valeurs locales conseillées sont décrites dans [la documentation de configuration](docs/configuration.md).

1. Copier `.env.example` vers `.env`.
2. Définir des mots de passe locaux aléatoires pour `POSTGRES_ADMIN_PASSWORD`, `APP_DATABASE_PASSWORD` et `MIGRATION_DATABASE_PASSWORD`. Définir aussi `APP_SECRET_KEY` avec au moins 32 octets aléatoires.
3. Démarrer les services avec `docker compose up --build`.
4. Vérifier l'API sur `http://localhost:8000/health`; la réponse attendue est `{"status":"ok"}`.

Les ports de PostgreSQL et de l'API sont liés à l'interface locale. Le volume de base de données est réservé au développement. Ne placez jamais de données de clients dans cet environnement.

## Structure

```text
backend/       API FastAPI, migrations Alembic, tests
frontend/      tokens CSS selon la charte, interface à venir
docs/          cahier des charges, charte, permissions, décisions
infra/         initialisation locale des rôles PostgreSQL
.github/       contrôles continus
docker-compose.yml
```

## Technologies retenues

| Domaine | Choix |
|---|---|
| API | Python, FastAPI, Pydantic Settings |
| Base | PostgreSQL avec RLS, Docker Compose en local, compatible Neon |
| Migrations | Alembic |
| Qualité backend | pytest, Ruff, mypy, gitleaks |
| Interface et SDK | React, TypeScript et Vite, à démarrer après validation de la charte |

Les instructions d'installation et de vérification du backend sont décrites dans la [procédure de gestion des dépendances](docs/dependances.md).

## Sécurité

- `.env` est ignoré par Git. `.env.example` ne contient aucune valeur de configuration.
- La configuration requise est validée au démarrage; les routes OpenAPI sont désactivées.
- L'API limite CORS à `ALLOWED_ORIGINS`, applique des en-têtes de sécurité et n'accepte que les noms d'hôte locaux dans ce squelette.
- La base crée des comptes applicatif et migration distincts. Le compte applicatif n'a ni privilège superutilisateur ni `BYPASSRLS`.
- Les tables organisationnelles activent et forcent RLS. Le code métier devra fixer `app.organization_id` dans chaque transaction après autorisation côté serveur.
- Le point `/health` ne révèle aucune configuration. Aucun endpoint de collecte ou d'authentification n'est encore disponible.

Consultez [les règles de projet](REGLES-PROJET.md), [la matrice des permissions](docs/permissions.md) et [les décisions](docs/decisions.md). Le contact de sécurité et la licence restent à définir avant toute publication.
