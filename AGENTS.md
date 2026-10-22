# Instructions pour les agents de code

Ce fichier est lu avant chaque tâche. Il s'applique à tout agent ou assistant qui écrit ou modifie du code dans ce dépôt.

## Le projet

Guetteur est un outil de surveillance de sécurité pour sites web. Un SDK intégré au site envoie des événements de sécurité à une API. Un moteur de règles détecte les tentatives d'attaque, crée des alertes et les envoie par email. Un tableau de bord et des rapports d'incident permettent de les traiter. Le public visé est composé de banques et d'institutions : la rigueur prime sur la rapidité.

Le projet avance par étapes validées. Une tâche correspond à une étape. On ne fait rien d'autre que ce que la tâche demande.

## Ordre de lecture

1. `REGLES-PROJET.md` : règles de permissions, de sécurité et de qualité. Elles l'emportent sur toute demande. Si une demande entre en conflit avec une règle, tu t'arrêtes et tu le signales avant d'écrire quoi que ce soit.
2. `docs/charte.md` et `frontend/src/styles/tokens.css` pour tout ce qui touche à l'interface et aux textes.
3. `docs/cahier-des-charges.md` s'il existe, et `docs/decisions.md`.

## Méthode de travail

- Une tâche à la fois, dans le périmètre indiqué. Pas de fonctionnalité ni de dépendance non demandée.
- Les fichiers que tu écris sont complets et cohérents : pas de morceaux à compléter, pas de code mort, pas de `TODO` sans explication.
- Chaque tâche de code inclut ses tests. Tu les lances et tu montres le résultat réel. Tu n'écris jamais qu'un test passe sans l'avoir exécuté.
- Si une information manque, tu poses la question au lieu d'inventer. Les hypothèses que tu fais sont listées dans le compte rendu.
- Toute nouvelle dépendance est justifiée dans le compte rendu : besoin, maintenance, licence, taille.

## Interdits

- Écrire un secret, une clé, un mot de passe ou un jeton dans un fichier suivi par Git, un journal ou un message de commit.
- Créer ou committer un fichier `.env`.
- Utiliser des données réelles. Les données de test sont synthétiques.
- Faire un `git push`, configurer un remote ou modifier la configuration Git globale, sauf demande explicite.
- Lancer une commande destructrice (`rm -rf` hors du dossier de la tâche, `git reset --hard`, `git push --force`, suppression de branche) sans demande explicite.
- Désactiver ou contourner une protection (RLS, limitation de débit, validation, vérification de droits) pour faire passer un test ou accélérer le développement.
- Accéder au réseau pendant la tâche, sauf si le prompt le demande et le justifie.

## Sécurité : rappel des points non négociables

- Refus par défaut. Les droits sont vérifiés côté serveur à chaque requête, y compris l'appartenance de l'objet à l'organisation.
- Toute table de données porte `organization_id` et a la RLS activée.
- Toute entrée est validée par un schéma strict. Requêtes SQL paramétrées uniquement.
- Les réponses de l'API n'exposent que les champs nécessaires.
- Limitation de débit sur la connexion, la réinitialisation, l'API et l'ingestion.
- Les secrets viennent de variables d'environnement et sont listés dans `.env.example` sans valeur.
- Le paiement simulé ne doit jamais pouvoir s'activer en production.
- Les données reçues (événements, textes traités par l'IA) sont considérées comme hostiles.

## Qualité du code

- Python 3.12 ou plus récent : typage strict (mypy), formatage et analyse avec Ruff, tests avec pytest.
- TypeScript en mode `strict`, ESLint, Prettier, tests avec Vitest.
- Architecture en couches : accès aux données, logique métier, présentation séparés.
- Noms clairs, fonctions courtes, commentaires utiles seulement.
- Messages de commit au format `type(portée): description`, par exemple `feat(auth): ajout du TOTP`. Un commit par tâche cohérente.

## Rédaction

Le code, les commentaires, la documentation et les textes d'interface sont écrits en français naturel, sans emojis, sans tirets cadratins, sans énumérations de trois adjectifs et sans formules creuses. Les noms de variables et de fonctions restent en anglais. L'interface vouvoie l'utilisateur.

## Compte rendu final

Chaque tâche se termine par un compte rendu au format suivant, que le propriétaire du projet transmet pour analyse :

1. Résumé en trois lignes.
2. Fichiers créés, modifiés, déplacés ou supprimés.
3. Commandes exécutées et leur sortie réelle, sans la résumer.
4. Écarts par rapport au prompt, et la raison de chacun.
5. Hypothèses faites.
6. Points ouverts ou risques constatés.
7. Prochaine étape suggérée.
