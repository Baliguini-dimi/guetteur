# Tests d'isolation PostgreSQL

Ces tests vérifient sur PostgreSQL réel que les droits et les politiques RLS isolent les données de chaque organisation.

## Ce que les tests vérifient

- Les rôles et les tables imposent les privilèges attendus et RLS est activée et forcée.
- Sans contexte, avec un contexte vide ou entre deux organisations, aucune ligne d'une autre organisation n'est visible.
- Les insertions, modifications, suppressions, contraintes étrangères et cascades suivent les droits définis pour les sites et les événements.
- Les quatre tables d'authentification isolent `users`, `backup_codes`, `sessions` et `audit_log`, leurs droits par colonne et leurs contraintes.
- `bootstrap_user` peut créer une organisation, un propriétaire et une entrée d'audit dans son contexte, mais ne peut lire aucune table ni créer des sessions ou des codes de secours.
- Les tables `organizations` et `alembic_version` restent inaccessibles en écriture ou en lecture à `app_user`, et le contexte n'est pas conservé après le commit.
- La désactivation de RLS dans la base de test fait échouer les contrôles d'isolation.

## Lancer les tests sur ce poste

Exécutez les commandes depuis la racine du dépôt avec PowerShell. Elles utilisent le port 55432 pour PostgreSQL afin d'éviter le port local 5432. Le résultat `False` au premier contrôle indique que 55432 est libre.

```powershell
Test-NetConnection -ComputerName 127.0.0.1 -Port 55432 -InformationLevel Quiet

function New-HexSecret {
    param([int]$ByteCount = 24)
    $buffer = New-Object byte[] $ByteCount
    $generator = New-Object System.Security.Cryptography.RNGCryptoServiceProvider
    $generator.GetBytes($buffer)
    $generator.Dispose()
    [BitConverter]::ToString($buffer).Replace('-', '')
}

$env:POSTGRES_ADMIN_PASSWORD = New-HexSecret
$env:APP_DATABASE_PASSWORD = New-HexSecret
$env:MIGRATION_DATABASE_PASSWORD = New-HexSecret
$env:BOOTSTRAP_DATABASE_PASSWORD = New-HexSecret
$env:APP_SECRET_KEY = New-HexSecret
$env:GUETTEUR_DB_PORT = '55432'
$env:GUETTEUR_API_PORT = '18000'
$env:ALLOWED_ORIGINS = 'http://localhost:5173'

docker compose -p guetteur-test up -d --wait db

$env:DATABASE_MIGRATION_URL = "postgresql+psycopg://migration_user:$($env:MIGRATION_DATABASE_PASSWORD)@db:5432/guetteur"
$env:TEST_DATABASE_ADMIN_URL = "postgresql://guetteur_admin:$($env:POSTGRES_ADMIN_PASSWORD)@db:5432/guetteur"
$env:TEST_DATABASE_APP_URL = "postgresql://app_user:$($env:APP_DATABASE_PASSWORD)@db:5432/guetteur"
$env:TEST_DATABASE_MIGRATION_URL = $env:DATABASE_MIGRATION_URL
$env:TEST_DATABASE_BOOTSTRAP_URL = "postgresql://bootstrap_user:$($env:BOOTSTRAP_DATABASE_PASSWORD)@db:5432/guetteur"
$backendPath = (Get-Location).Path + '\backend'

docker run --rm --name guetteur-final-integration --network guetteur-test_default --mount 'type=volume,source=guetteur-pip-cache,target=/root/.cache/pip' -v "${backendPath}:/source:ro" -e DATABASE_MIGRATION_URL -e TEST_DATABASE_ADMIN_URL -e TEST_DATABASE_APP_URL -e TEST_DATABASE_MIGRATION_URL -e TEST_DATABASE_BOOTSTRAP_URL -e APP_SECRET_KEY -e APP_ENV=test python@sha256:48a11b7ba705fd53bf15248d1f94d36c39549903c5d59edcfa2f3f84126e7b44 sh -lc "mkdir -p /tmp/work && tar --exclude=.venv --exclude=__pycache__ --exclude=.mypy_cache --exclude=.pytest_cache --exclude=.ruff_cache -C /source -cf - . | tar -C /tmp/work -xf - && cd /tmp/work && python -m venv /tmp/venv && /tmp/venv/bin/python -m pip install --require-hashes --default-timeout=120 --retries 5 -r requirements-dev.lock && export PYTHONPATH=/tmp/work/src && /tmp/venv/bin/alembic upgrade head && /tmp/venv/bin/alembic downgrade -1 && /tmp/venv/bin/alembic upgrade head && /tmp/venv/bin/pytest -o addopts= -m integration -rs -vv"

docker run --rm --name guetteur-checks --network guetteur-test_default --mount 'type=volume,source=guetteur-pip-cache,target=/root/.cache/pip' -v "${backendPath}:/source:ro" -e TEST_DATABASE_ADMIN_URL -e TEST_DATABASE_APP_URL -e TEST_DATABASE_MIGRATION_URL -e TEST_DATABASE_BOOTSTRAP_URL -e APP_SECRET_KEY -e APP_ENV=test python@sha256:48a11b7ba705fd53bf15248d1f94d36c39549903c5d59edcfa2f3f84126e7b44 sh -lc "mkdir -p /tmp/work && tar --exclude=.venv --exclude=__pycache__ --exclude=.mypy_cache --exclude=.pytest_cache --exclude=.ruff_cache -C /source -cf - . | tar -C /tmp/work -xf - && cd /tmp/work && python -m venv /tmp/venv && /tmp/venv/bin/python -m pip install --require-hashes --default-timeout=120 --retries 5 -r requirements-dev.lock && export PYTHONPATH=/tmp/work/src && /tmp/venv/bin/ruff check . && /tmp/venv/bin/mypy src && /tmp/venv/bin/pytest"
```

Les URL sont construites dans l'environnement PowerShell et transmises au conteneur par nom de variable. N'affichez pas leur contenu. Les tests utilisent l'hôte `db` et le port interne 5432 du réseau Compose, jamais le port publié sur le poste.

Après une vérification normale, vous pouvez tester le contrôle négatif sur la seule base `guetteur-test` :

```powershell
docker compose -p guetteur-test exec -T db psql -U guetteur_admin -d guetteur -c "ALTER TABLE users DISABLE ROW LEVEL SECURITY;"
```

Relancez ensuite le conteneur `guetteur-final-integration` avec la commande ci-dessus. Plusieurs tests doivent échouer. Réinitialisez immédiatement la base avant toute autre utilisation :

```powershell
docker compose -p guetteur-test down -v
docker compose -p guetteur-test up -d --wait db
```

Relancez alors le conteneur `guetteur-final-integration` pour appliquer la migration et confirmer que les tests repassent. Terminez toujours par :

```powershell
docker compose -p guetteur-test down -v
```

## Lire un échec

Un échec RLS signale une ligne visible ou une opération autorisée au mauvais endroit. Un SQLSTATE `42501` indique un refus de privilège ou de politique RLS; `23503` indique le refus de la clé étrangère composite; `22P02` indique que le contexte fourni n'est pas un UUID.

Si un test échoue dans une exécution normale, conservez sa sortie et vérifiez l'état de la base et les variables de connexion sans les afficher. Ne modifiez pas le test ou la migration pour masquer l'échec. La correction des droits ou de la migration doit faire l'objet d'une étape validée distincte.
