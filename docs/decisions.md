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

La version cible est Python 3.12 pour la CI et Docker. Le poste de développement utilise Python 3.14.3. Les dépendances installées dans `backend/.venv` ont produit `requirements.lock`; la compatibilité avec Python 3.12 reste à confirmer par la CI et un test en conteneur.

## 22 octobre 2026 - D12 : dépôt

Le projet est un monorepo privé nommé `guetteur`.

## 22 octobre 2026 - D13 : première exécution de la CI

Le contrôle backend a réussi sous Python 3.12. Le contrôle des secrets a échoué faute de `GITHUB_TOKEN`, puis a été corrigé. `requirements.lock` a été généré sous Windows et Python 3.14 : il omet `greenlet`, que pip a installé sans version fixée sous Python 3.12. Le fichier sera régénéré dans un conteneur Python 3.12 sous Linux, et les dépendances d'exécution seront séparées de celles de développement.

## 22 octobre 2026 - D14 : épinglage des actions

Les actions GitHub tierces sont épinglées par SHA et Dependabot les met à jour. `gitleaks-action` reste sur son tag `@v2` en attendant la récupération de son SHA.

## Points ouverts

- Choisir l'hébergement de test.
- Choisir le fournisseur email.
- Définir le contact de sécurité.
- Choisir la licence.
