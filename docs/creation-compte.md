# Créer le premier compte propriétaire

La commande `create-owner` crée la première organisation et son compte propriétaire. Elle utilise le rôle PostgreSQL restreint `bootstrap_user`, qui n'est jamais transmis à l'API. Exécutez-la uniquement après avoir démarré PostgreSQL et appliqué les migrations.

Le mot de passe est saisi deux fois sans affichage. Il doit contenir entre 12 et 128 caractères après normalisation Unicode NFKC. La commande refuse les mots de passe qui contiennent la partie locale de l'adresse email, qui figurent dans sa liste locale ou qui sont des répétitions ou des suites faciles à deviner. La liste locale est minimale, rédigée à la main et sera remplacée par une liste vérifiée.

Depuis la racine du dépôt, après avoir renseigné les variables de connexion dans votre session PowerShell, construisez l'URL du rôle bootstrap et lancez le conteneur interactif de l'API sur le réseau Compose par défaut :

```powershell
$env:BOOTSTRAP_DATABASE_URL = "postgresql://bootstrap_user:$($env:BOOTSTRAP_DATABASE_PASSWORD)@db:5432/guetteur"
docker run --rm -it --network guetteur_default -e BOOTSTRAP_DATABASE_URL --entrypoint python guetteur-api:latest -m guetteur.cli create-owner
Remove-Item Env:BOOTSTRAP_DATABASE_URL
```

La commande demande le nom de l'organisation, l'adresse email et le mot de passe. Aucun mot de passe n'est fourni comme argument. Si votre projet Compose utilise un autre nom de projet, remplacez `guetteur_default` par le nom de son réseau.

À la fin, reportez l'identifiant affiché dans `OWNER_ORGANIZATION_ID`, côté serveur. Ne transmettez jamais `BOOTSTRAP_DATABASE_URL` au service `api`.

Point ouvert pour la V1a : ajouter une commande serveur pour réinitialiser le mot de passe du propriétaire.
