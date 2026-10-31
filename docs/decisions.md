# Décisions du projet

Ce fichier consigne les choix validés et les points encore ouverts. Les décisions sont datées en UTC.

## 22 octobre 2026 - D1 : nom du produit

Guetteur est le nom choisi par Dimitri malgré des réserves : le mot a une connotation particulière en français et passe mal à l'international. Les alternatives étudiées sont Sentinelle, proche de Microsoft Sentinel et SentinelOne, Mirador et Beffroi. La vérification de disponibilité du domaine, du nom GitHub, des résultats de recherche web et de la marque à l'OAPI reste à faire.

## 22 octobre 2026 - D2 : découpage

La V1a comprend la collecte par SDK, huit règles de détection, les alertes email, le tableau de bord et la sécurité complète. La V1b comprend les comptes et plans, le paiement simulé, la démonstration, WhatsApp et la détection par IA en mode fantôme.

## 22 octobre 2026 - D3 : stack

Le backend utilise Python, FastAPI, Pydantic et Alembic. Le frontend utilise React, TypeScript, Vite et Tailwind. PostgreSQL fonctionne dans Docker en local et sera hébergé chez Neon pour les tests en ligne. Supabase et NestJS ont été étudiés comme alternatives.

## 22 octobre 2026 - D4 : collecte

La collecte utilise un SDK TypeScript, car le portfolio de test est hébergé sur Vercel, où les Log Drains sont réservés aux offres payantes. Un collecteur de logs pourra être ajouté plus tard en option.

## 22 octobre 2026 - D5 : isolation

Toute table de données porte un `organization_id`. La RLS est activée et forcée dès la V1a.

## 22 octobre 2026 - D6 : droits en base

`app_user` ne reçoit que des GRANT explicites accordés par les migrations. `log_events` est en ajout seul. La purge de rétention passera par un rôle dédié à créer. Exception à l'ajout seul : la suppression d'un site ou d'une organisation supprime ses événements par cascade, car les contrôles d'intégrité de PostgreSQL ignorent la RLS.

## 22 octobre 2026 - D7 : paiement

Le paiement est simulé derrière une interface `PaymentProvider` et ne peut jamais être activé en production.

## 22 octobre 2026 - D8 : IA

La détection d'anomalies démarre en mode fantôme. L'explication des alertes sur des données masquées viendra ensuite.

## 22 octobre 2026 - D9 : design

L'interface est claire et institutionnelle, et s'adresse à l'utilisateur en le vouvoyant. Les polices sont Source Serif 4 et IBM Plex Sans. La charte et le vouvoiement ont été validés par Dimitri le 22 octobre 2026.

## 22 octobre 2026 - D10 : configuration

L'application lit uniquement les variables d'environnement du processus et ne lit pas de fichier `.env`. `.env.example` liste les noms sans valeurs. Les valeurs locales conseillées figurent dans `docs/configuration.md`.

## 22 octobre 2026 - D11 : Python

La version cible est Python 3.12 pour la CI et Docker. Le poste de développement utilise Python 3.14.3. Les dépendances installées dans `backend/.venv` ont produit `requirements.lock`. La compatibilité Python 3.12 est confirmée par la CI et par l'exécution en conteneur, et le lock a été régénéré sous Linux avec Python 3.12.

## 22 octobre 2026 - D12 : dépôt

Le projet est un monorepo privé nommé `guetteur`.

## 22 octobre 2026 - D13 : première exécution de la CI

Le contrôle backend a réussi sous Python 3.12. Le contrôle des secrets a échoué faute de `GITHUB_TOKEN`, puis a été corrigé. `requirements.lock` a été généré sous Windows et Python 3.14 : il omet `greenlet`, que pip a installé sans version fixée sous Python 3.12. Les dépendances d'exécution sont maintenant séparées de celles de développement. La compatibilité Python 3.12 est confirmée par la CI et par l'exécution en conteneur, et le lock a été régénéré sous Linux avec Python 3.12.

## 22 octobre 2026 - D14 : épinglage des actions

Les actions GitHub tierces sont épinglées par SHA et Dependabot les met à jour. `gitleaks-action` reste sur son tag `@v2` en attendant la récupération de son SHA.

## 22 octobre 2026 - D15 : locks Python 3.12

Les locks d'exécution et de développement sont régénérés sous Linux avec Python 3.12.9 et `pip-tools` 7.6.2. Ils utilisent des empreintes et incluent `greenlet`. L'extra de développement fixe `pip-audit` en version 2.10.1, publiée le 10 juin 2026.

## 22 octobre 2026 - D16 : image Docker reproductible

L'image `python:3.12.9-slim` est épinglée par le digest `sha256:48a11b7ba705fd53bf15248d1f94d36c39549903c5d59edcfa2f3f84126e7b44`. Le Dockerfile installe le lock avec empreintes, utilise un utilisateur non root, inclut les migrations, expose un contrôle de santé et applique le durcissement du conteneur dans Compose.

## 22 octobre 2026 - D17 : contrôles CI

La CI installe les dépendances de développement avec le lock et les empreintes, exécute `pip-audit` sur les dépendances d'exécution, épingle `gitleaks` par SHA et limite chaque job à dix minutes.

## 22 octobre 2026 - D18 : correction des vulnérabilités Starlette

`pip-audit 2.10.1` a signalé 14 entrées, soit 7 avis distincts (PYSEC-2026-161, 248, 249, 1941, 1942, 2280 et 2281) sur `starlette 0.46.2`, parmi 26 dépendances examinées. Les versions corrigées indiquées vont jusqu'à `1.3.1`, qui corrige également les autres avis. FastAPI passe de `0.115.12` à `0.143.0` et Starlette à `1.3.1`. Starlette reste une dépendance directe, car `backend/src/guetteur/main.py` importe `TrustedHostMiddleware` et le middleware de base depuis Starlette. L'audit du nouveau lock examine 28 dépendances et ne relève aucune vulnérabilité connue.

FastAPI `0.143.0` demande `annotated-doc>=0.0.2` et `opentelemetry-api>=1.44.0`, ajoutés au lock d'exécution. Les versions verrouillées sont `annotated-doc 0.0.5` (publiée le 28 juillet 2026, licence MIT) et `opentelemetry-api 1.45.1` (publiée le 6 octobre 2026, licence Apache-2.0).

Le résultat nul d'un audit temporaire précédent venait d'un export PowerShell avec `Set-Content -NoNewline`, qui avait concaténé les lignes et laissé zéro dépendance à examiner. Aucune vulnérabilité ne doit être ignorée sans être consignée dans les décisions du projet. Chaque audit doit afficher le nombre de dépendances examinées et vérifier qu'il correspond au nombre de paquets du lock.

## 28 octobre 2026 - D19 : tests d'isolation sur PostgreSQL

Les tests d'intégration exécutés sur PostgreSQL 17.4 confirment les rôles, les indicateurs RLS, l'isolation entre deux organisations, les refus d'écriture et les droits sur `alembic_version`. Les 23 tests d'intégration réussissent après migration sur une base neuve. La fonction de contexte utilise `set_config('app.organization_id', ..., true)` : le contexte disparaît au commit. La suppression d'un site supprime ses événements par cascade, conformément à D6. Le contrôle négatif, effectué après désactivation de RLS sur `sites` dans la seule base de test, produit 10 échecs et 13 réussites; après réinitialisation et nouvelle migration, les 23 tests réussissent. Le job CI `isolation` exécute ces tests sur PostgreSQL. La vérification HSTS confirme l'absence de l'en-tête en environnement `local` et sa présence en `production`.

## 28 octobre 2026 - D20 : création des organisations et purge

`app_user` ne reçoit aucun droit `INSERT` sur `organizations`. La création de la première organisation passe par le rôle restreint `bootstrap_user`, validé en D23. La purge de rétention devra utiliser un rôle dédié à concevoir; ce point reste ouvert.

## 28 octobre 2026 - D21 : ports locaux configurables

Les ports publiés par Docker Compose sont configurables avec `GUETTEUR_DB_PORT` et `GUETTEUR_API_PORT`, avec les valeurs par défaut 5432 et 8000. Cette possibilité répond au conflit de port 5432 signalé sur le poste. Le programme extérieur n'a pas été arrêté ni modifié. Le diagnostic de cette exécution n'a trouvé aucun écouteur Windows sur 5432 ou 8000, tandis que `Test-NetConnection` vers 5432 a répondu `True`.

## 31 octobre 2026 - D22 : tables d'authentification

La migration 0002 crée `users`, `backup_codes`, `sessions` et `audit_log`, toutes isolées par `organization_id`, avec RLS activée et forcée. L'adresse de `users` est en minuscules et unique globalement. `app_user` reçoit des droits de mise à jour par colonne sur `users`, `sessions` et `backup_codes`; `audit_log` reste en ajout seul. Les sessions provisoires sont révoquées plutôt que supprimées, car `app_user` n'a aucun droit de suppression sur cette table. `audit_log.user_id` n'a pas de clé étrangère afin que l'historique survive à la suppression d'un compte.

## 31 octobre 2026 - D23 : rôle bootstrap_user

`bootstrap_user` reçoit uniquement les droits d'insertion nécessaires, avec des politiques réservées à ce rôle. Il ne peut jamais lire les tables et son mot de passe n'est transmis qu'à la commande d'installation, jamais à l'API. La création du premier compte par cette commande sera réalisée à l'étape suivante.

## 31 octobre 2026 - D24 : validation de la conception d'authentification

Dimitri valide la note `docs/conception-authentification.md` et ses décisions A1 à A10. Les dépendances `argon2-cffi`, `pyotp` et `cryptography` seront ajoutées et verrouillées lors des étapes qui les utiliseront.

## Points ouverts

- Choisir l'hébergement de test.
- Choisir le fournisseur email.
- Définir le contact de sécurité.
- Choisir la licence.
