# Dépendances Python

Le backend utilise Python 3.12. Les dépendances sont verrouillées dans `backend/requirements.lock` pour l'exécution et dans `backend/requirements-dev.lock` pour l'exécution et les contrôles de développement. Les deux fichiers contiennent des empreintes.

## Régénérer les locks

La régénération se fait dans l'image Linux `python:3.12.9-slim`. La commande utilisée pour installer `pip-tools` est la suivante :

```powershell
docker run --rm --name guetteur-locks -v "${PWD}\backend:/work" -w /work python:3.12.9-slim sh -lc "python -m pip install pip-tools && pip-compile --generate-hashes --output-file=requirements.lock pyproject.toml && pip-compile --generate-hashes --extra=dev --output-file=requirements-dev.lock pyproject.toml && pip-compile --version"
```

La version utilisée est `pip-tools 7.6.2`. La première commande produit uniquement les dépendances d'exécution. La seconde ajoute l'extra `dev`.

Après régénération, vérifier la présence de `greenlet` et des empreintes :

```powershell
Select-String -Path backend/requirements.lock,backend/requirements-dev.lock -Pattern '^greenlet==','--hash=sha256:'
```

## Vérifier le backend dans un environnement propre

La vérification testée utilise un environnement virtuel créé dans un conteneur jetable :

```powershell
docker run --rm --name guetteur-checks -v "${PWD}\backend:/work" -w /work python:3.12.9-slim sh -lc "python -m venv /tmp/venv && /tmp/venv/bin/python -m pip install --require-hashes -r requirements-dev.lock && /tmp/venv/bin/python -m pip install --no-deps . && /tmp/venv/bin/ruff check . && /tmp/venv/bin/mypy src && /tmp/venv/bin/pytest"
```

Cette commande installe le lock avec `--require-hashes`, installe le paquet sans ses dépendances, puis exécute Ruff, mypy et pytest. Les caches et les artefacts de construction sont ignorés par Git.

## Auditer les dépendances d'exécution

La CI utilise `pip-audit 2.10.1` avec le fichier d'exécution :

```powershell
docker run --rm --name guetteur-pipaudit -v "${PWD}\backend:/work" -w /work python:3.12.9-slim sh -lc "python -m pip install pip-audit==2.10.1 && pip-audit --require-hashes --format json -r requirements.lock"
```

La commande vérifie les empreintes du fichier pendant l'audit. Dans le JSON, la longueur de `dependencies` doit correspondre au nombre de paquets épinglés dans le lock. Vérifier ce nombre avant d'interpréter le résultat; un résultat non nul signale les vulnérabilités détectées et doit être traité avant la fusion.

Sous Windows PowerShell 5.1, ne créez pas le fichier temporaire du lock par redirection simple, qui peut produire un fichier UTF-16 illisible par l'auditeur. Utilisez `git show HEAD:backend/requirements.lock | Out-File -Encoding ascii <fichier temporaire>` et ne mettez pas `-NoNewline`, qui concatène toutes les lignes et peut faire examiner zéro dépendance.

## Relever le digest de l'image

Le digest utilisé par le Dockerfile se relève avec :

```powershell
docker pull python:3.12.9-slim
docker image inspect python:3.12.9-slim --format '{{index .RepoDigests 0}}'
```

Le résultat validé pour cette étape est `python@sha256:48a11b7ba705fd53bf15248d1f94d36c39549903c5d59edcfa2f3f84126e7b44`.
