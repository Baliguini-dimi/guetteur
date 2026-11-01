# Conception : authentification du propriétaire (V1a)

Projet Guetteur. Auteur : Dimitri Nelson Baliguini Demba. Version 0.1, à valider avant tout code. Fichier prévu pour `docs/conception-authentification.md`.

## 1. Objet

Permettre au propriétaire d'une installation de se connecter de façon sûre pour consulter ses alertes et gérer son site. C'est la première fonctionnalité qui manipule des secrets : elle doit respecter `REGLES-PROJET.md` (sections 3, 4, 5, 6 et 11) sans exception.

**Dans le périmètre de la V1a** : création du premier compte par une commande, connexion par mot de passe, double authentification obligatoire, sessions, déconnexion, changement de mot de passe, limitation des tentatives, journal d'audit.

**Hors périmètre** : inscription libre, réinitialisation par email (la V1a n'a pas encore l'envoi d'email), connexion par un compte externe (Google, Microsoft), clés d'accès (passkeys), gestion de plusieurs membres. Ces points viennent en V1b ou plus tard.

## 2. Termes utilisés

- **Hachage de mot de passe** : transformation à sens unique. On ne stocke jamais le mot de passe, seulement son empreinte.
- **Argon2id** : algorithme de hachage conçu pour être lent et gourmand en mémoire, ce qui décourage les attaques par essais massifs.
- **Double authentification (2FA, TOTP)** : après le mot de passe, un code à six chiffres, valable trente secondes, généré par une application sur le téléphone.
- **Session** : l'état « connecté » conservé par le serveur après la connexion, identifié par un cookie.
- **CSRF** : attaque qui pousse un utilisateur connecté à effectuer une action à son insu depuis un autre site.
- **Rate limiting** : limite du nombre d'essais sur une période.
- **Énumération de comptes** : deviner quelles adresses ont un compte d'après les réponses du site.

## 3. Décisions à valider

| N° | Sujet | Proposition | Pourquoi | Alternative |
|---|---|---|---|---|
| A1 | Mots de passe | 12 caractères minimum, 128 maximum, refus d'une liste de mots de passe courants et de l'adresse email, collage autorisé | Conforme à la section 4 des règles ; la longueur compte plus que les symboles | Vérifier aussi contre une liste publique de fuites : demande un appel externe, à éviter dans la version installée chez le client |
| A2 | Hachage | Argon2id avec au moins 19 Mio de mémoire, 2 itérations, 1 voie, réglés ensuite sur le serveur cible pour viser 0,3 à 0,5 seconde | Valeurs minimales recommandées par l'OWASP | Paramètres plus lourds si le serveur le permet |
| A3 | Double authentification | Obligatoire pour le propriétaire dès la première connexion. Dix codes de secours à usage unique. Un code ne peut pas être rejoué | Règle de la section 4 ; un mot de passe seul ne suffit pas pour un outil de sécurité | Clés d'accès (passkeys) à ajouter plus tard |
| A4 | Sessions | Stockées côté serveur. Cookie `__Host-session`, `HttpOnly`, `Secure`, `SameSite=Strict`. Expiration après 30 minutes d'inactivité ou 12 heures au total. Nouvel identifiant à chaque connexion | Un cookie volé reste limité dans le temps ; la déconnexion est réellement effective | Jetons JWT : plus difficiles à révoquer, donc écartés |
| A5 | Limitation | 5 tentatives par minute et par adresse IP, 10 par quinze minutes et par compte, délai croissant, verrouillage temporaire jamais définitif | Valeurs de la section 6 des règles | Compteurs partagés (Redis) dès qu'il y a plusieurs instances |
| A6 | Création du premier compte | Une commande en ligne de commande exécutée sur le serveur, avec un rôle de base de données dédié `bootstrap_user`, dont le mot de passe n'est jamais donné à l'API | Aucune page d'inscription ouverte au public ; ferme le point ouvert de D20 | Assistant web d'installation : plus exposé, écarté |
| A7 | Mot de passe oublié | Commande en ligne de commande sur le serveur pour la V1a ; réinitialisation par email en V1b | Évite de bâtir l'envoi d'email avant l'étape prévue | Aucune |
| A8 | Organisation à la connexion | En V1a, une installation sert une seule organisation, dont l'identifiant est donné par un paramètre non secret `OWNER_ORGANIZATION_ID`. En V1b, on choisit entre adresse de l'organisation (sous-domaine) et fonction de recherche dédiée | Simple et sûr pour la V1a ; la décision V1b est prise plus tard | Décider maintenant : plus de travail pour rien |
| A9 | Cookie et organisation | Le cookie contient l'identifiant de l'organisation et un secret aléatoire de 256 bits. On fixe le contexte d'organisation à partir du cookie, puis on retrouve la session par l'empreinte du secret | Un identifiant d'organisation falsifié ne sert à rien sans le secret | Table de sessions lisible sans contexte : brèche possible |
| A10 | Dépendances nouvelles | `argon2-cffi`, `pyotp`, `cryptography` | Bibliothèques établies pour chaque besoin ; versions exactes, verrouillées avec empreintes, auditées par `pip-audit`, publiées depuis plus de 14 jours | Écrire soi-même la cryptographie : à proscrire |

## 4. Parcours de connexion

1. Le propriétaire saisit son adresse et son mot de passe.
2. Le serveur applique d'abord la limitation de débit. Il calcule toujours une empreinte, même si l'adresse n'existe pas, pour que le temps de réponse ne révèle rien.
3. En cas d'échec, le message est toujours le même : « Identifiants invalides ».
4. Si le mot de passe est bon, le serveur ouvre une session provisoire valable cinq minutes, qui ne donne accès qu'à la saisie du code.
5. Le propriétaire saisit le code à six chiffres, ou un code de secours.
6. Le serveur crée alors la vraie session avec un nouvel identifiant, supprime la session provisoire et enregistre l'événement dans le journal d'audit.
7. À la toute première connexion, le propriétaire est obligé d'enregistrer son application de double authentification avant tout autre écran.

## 5. Données à créer (migration 0002)

Toutes les tables portent `organization_id`, la RLS activée et forcée, des droits explicites, comme les tables existantes.

- **users** : identifiant, organization_id, adresse email en minuscules, empreinte du mot de passe, rôle, secret TOTP chiffré, date d'activation du TOTP, dernier pas de temps accepté, date de création, dernière connexion, date de désactivation.
- **backup_codes** : identifiant, user_id, empreinte du code, date d'utilisation.
- **sessions** : identifiant, organization_id, user_id, empreinte du secret, étape (provisoire ou complète), dates de création, de dernière activité et d'expiration, date de révocation, empreinte de l'agent utilisateur.
- **audit_log** : en ajout seul, comme `log_events`. Il enregistre les connexions réussies et échouées, l'activation ou la désactivation de la double authentification, les changements de mot de passe, les révocations de sessions.

Le rôle `bootstrap_user` n'a que le droit d'insertion nécessaire pour créer l'organisation et le premier utilisateur. `app_user` ne reçoit aucun droit de suppression sur `audit_log`, et aucun droit sur les données d'un autre rôle.

## 6. Points d'accès de l'API

- `POST /auth/login` : adresse et mot de passe.
- `POST /auth/login/totp` : code de la double authentification ou code de secours.
- `POST /auth/logout`.
- `GET /auth/me` : renvoie uniquement le nécessaire (adresse, rôle, état de la double authentification).
- `POST /auth/password` : changement du mot de passe, avec nouvelle authentification ; révoque les autres sessions.
- `POST /auth/totp/setup` et `POST /auth/totp/confirm`.
- `GET /auth/sessions` et `DELETE /auth/sessions/{id}` : voir et révoquer ses sessions.

Chaque point d'accès valide ses entrées par un schéma strict, répond avec des erreurs uniformes sans détail interne, et exige un jeton CSRF pour toute action qui modifie un état.

## 7. Menaces visées et réponse prévue

| Menace | Réponse |
|---|---|
| Essais massifs de mots de passe sur un compte | Limitation par compte et par IP, délai croissant, double authentification obligatoire |
| Mots de passe volés ailleurs et réessayés ici | Limitation par IP, double authentification, empreintes lentes |
| Deviner quelles adresses ont un compte | Même message, même durée de traitement |
| Vol du cookie | Cookie `HttpOnly` et `Secure`, durée limitée, empreinte de l'agent enregistrée, révocation possible |
| Fixation de session | Nouvel identifiant à chaque connexion et après la double authentification |
| Action forcée depuis un autre site | `SameSite=Strict` et jeton CSRF |
| Fuite de la base de données | Aucun mot de passe en clair, secrets TOTP chiffrés, sessions stockées sous forme d'empreinte |
| Code TOTP rejoué | Dernier pas de temps accepté mémorisé par utilisateur |
| Détournement de la commande de création de compte | Rôle `bootstrap_user` isolé de l'API, mot de passe saisi au clavier, jamais en argument de commande |
| Journal modifié après une intrusion | Table en ajout seul, comme les événements |

## 8. Tests exigés

- **Unitaires** : paramètres Argon2id, refus de mots de passe faibles, génération et validation du TOTP avec une horloge simulée, rejeu refusé.
- **Intégration sur PostgreSQL**, ajoutés au dispositif existant : la RLS isole `users`, `sessions` et `audit_log` ; `app_user` ne peut ni supprimer ni modifier le journal ; `bootstrap_user` ne peut rien lire ; une session d'une autre organisation n'est jamais retrouvée.
- **Interface de programmation** : message identique pour adresse inconnue et mauvais mot de passe, limitation effective, cookie avec les bons attributs, nouvel identifiant à chaque connexion, session invalide après déconnexion, après changement de mot de passe et après expiration, refus sans jeton CSRF.
- **Contrôle négatif**, comme pour l'isolation : désactiver une protection fait échouer les tests concernés.

## 9. Découpage en étapes

Chaque étape fait l'objet d'un prompt validé, d'une branche et d'une demande de fusion.

1. Migration 0002 (tables, rôle `bootstrap_user`, droits) et tests d'isolation étendus.
2. Mots de passe : hachage, règles, commande de création du premier compte.
3. Sessions : cookie, stockage, expiration, CSRF.
4. Connexion et limitation des tentatives.
5. Double authentification et codes de secours.
6. Journal d'audit et écran de connexion (charte, états de chargement et d'erreur).

## 10. Questions ouvertes

- Choix de la liste locale de mots de passe courants (source à vérifier pour sa licence).
- Gestion de l'adresse IP réelle derrière un serveur intermédiaire (liste de serveurs de confiance).
- Clé de chiffrement des secrets TOTP : variable d'environnement en V1a, coffre de clés plus tard.
- Procédure de la V1b pour trouver l'organisation d'un utilisateur à la connexion.
