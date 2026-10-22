# Règles de projet : permissions, sécurité et qualité

Auteur : Dimitri Nelson Baliguini Demba. Version 1.0.

## 0. Comment utiliser ce fichier

Ce fichier est la ligne directrice de tous mes projets. On le copie à la racine de chaque dépôt, sous le nom `REGLES-PROJET.md`. Il s'applique à moi et à toute personne ou tout assistant (y compris une IA) qui écrit du code pour le projet.

- Sauf mention contraire, chaque règle est obligatoire.
- Les chiffres donnés (tailles, durées, limites) sont des valeurs par défaut. On les ajuste par projet, et on écrit l'ajustement dans `docs/decisions.md` avec la raison.
- Si une demande entre en conflit avec une règle, on applique la règle et on le signale. Seul le propriétaire du projet peut modifier ce fichier.
- Quand un terme technique est utilisé, il est défini dans le glossaire en fin de fichier.

## 1. Principes

1. **Refus par défaut.** Rien n'est autorisé tant que ce n'est pas écrit explicitement.
2. **Moindre privilège.** Chaque personne, compte, clé et service reçoit uniquement ce dont il a besoin.
3. **Le serveur décide.** Tout ce qui vient du navigateur ou d'un client est considéré comme non fiable.
4. **Défense en profondeur.** Plusieurs protections superposées : si l'une tombe, une autre retient.
5. **Montrer le strict nécessaire.** Une donnée qui n'a pas besoin d'être affichée n'est pas envoyée.
6. **Tout est vérifiable.** Une règle sans test ou sans contrôle automatique est une intention, pas une règle.
7. **Simple d'abord.** Pas de fonctionnalité ni de dépendance sans besoin validé.

## 2. Méthode de travail

- On avance fichier par fichier, avec confirmation à chaque étape.
- Les fichiers sont livrés complets, pas en morceaux de différences.
- Chaque étape a un livrable, des tests et une validation avant la suivante.
- Les textes, l'interface et la documentation sont écrits dans un français naturel : pas d'emojis, pas de tirets cadratins, pas d'énumérations de trois adjectifs, pas de superlatifs creux.
- L'interface reste sobre : pas de dégradés décoratifs, pas de symboles génériques, pas de composants qui ressemblent à un modèle générique.

## 3. Permissions et contrôle d'accès

- Toute route et toute action exigent une autorisation explicite côté serveur. Masquer un bouton dans l'interface n'est jamais une protection.
- À chaque requête, le serveur vérifie trois choses : qui est l'utilisateur, à quelle organisation il appartient, et s'il a le droit d'agir sur cet objet précis.
- Un identifiant envoyé par le client n'est jamais cru sur parole : on vérifie que l'objet appartient bien à l'organisation de l'utilisateur (protection contre l'IDOR).
- Rôles de base : propriétaire, administrateur, membre, lecteur. La matrice des permissions est écrite dans `docs/permissions.md` et couverte par des tests.
- Les actions sensibles (changer l'email ou le mot de passe, gérer les clés API, la facturation, supprimer des données) demandent une nouvelle authentification.
- Pas de compte partagé. Les comptes de service ont des droits minimaux et un nom explicite.
- Les réponses de l'API n'exposent que les champs nécessaires, via des schémas de sortie explicites. On ne renvoie jamais un objet de base de données brut. Les champs internes (hash, notes internes, identifiants techniques) sont exclus.
- Pour l'objet d'une autre organisation, on répond 404 et non 403, afin de ne pas révéler son existence.
- Chaque nouvelle route s'accompagne d'un test qui prouve qu'un utilisateur d'une autre organisation n'y accède pas.

## 4. Authentification et sessions

**Mots de passe**
- Hachage avec Argon2id. Jamais de MD5 ni de SHA seul.
- 12 caractères minimum, 128 acceptés. Pas de règles de composition artificielles : la longueur compte plus que les symboles.
- Refus des mots de passe courants ou déjà compromis (vérification par k-anonymat avec Have I Been Pwned, ou liste locale).
- Le collage est autorisé pour permettre les gestionnaires de mots de passe.

**Connexion**
- Double authentification (TOTP) obligatoire pour les propriétaires et administrateurs, recommandée pour tous. Codes de secours fournis à l'activation.
- Limitation des tentatives par compte et par IP, avec délai croissant et verrouillage temporaire, jamais définitif.
- Messages génériques : « Identifiants invalides », « Si ce compte existe, un email a été envoyé ».
- Vérification de l'adresse email à l'inscription.
- Protection anti-bot sur les formulaires publics (Cloudflare Turnstile ou équivalent respectueux de la vie privée) en plus d'un champ piège (honeypot).

**Réinitialisation**
- Jeton aléatoire à usage unique, stocké haché, valable 30 minutes. L'utiliser invalide toutes les sessions ouvertes.

**Sessions**
- Cookies `HttpOnly`, `Secure`, `SameSite=Lax` ou `Strict`.
- Identifiant de session aléatoire, renouvelé à la connexion et à toute élévation de privilèges.
- Expiration d'inactivité (30 minutes pour les administrateurs) et durée maximale (12 heures par défaut).
- La déconnexion invalide la session côté serveur. L'utilisateur voit ses sessions actives et peut les révoquer.
- Si des JWT sont utilisés : durée de vie de 15 minutes maximum, refresh token rotatif et révocable, algorithme imposé côté serveur, aucun stockage dans le `localStorage`.
- Un email prévient l'utilisateur lors d'une connexion depuis un nouvel appareil et lors de tout changement de mot de passe ou d'adresse.

## 5. Secrets et clés

- Aucun secret dans le code, les logs, les captures d'écran, les messages de commit ou les tickets.
- Le fichier `.env` est dans `.gitignore` dès le premier commit. Un fichier `.env.example` liste les noms des variables, sans valeurs.
- Chaque environnement (local, test, production) a ses propres secrets.
- En ligne, les secrets vivent dans le gestionnaire de secrets de la plateforme de déploiement. En local, dans un `.env` jamais partagé.
- Un scan automatique de secrets (gitleaks) tourne avant chaque commit et dans l'intégration continue.
- Rotation tous les 90 jours pour les secrets critiques, et immédiate au moindre doute.
- Côté navigateur, seules les clés conçues pour être publiques sont autorisées (par exemple une clé publique de paiement, ou la clé `anon` d'une base protégée par RLS). Toute variable exposée au navigateur (préfixe `VITE_`, `NEXT_PUBLIC_`) est considérée comme publique.
- La clé de service (`service_role`), les clés privées et les jetons d'API ne quittent jamais le serveur.

**Clés API émises par l'application**
- Au moins 32 octets aléatoires, avec un préfixe lisible (par exemple `sk_live_`).
- Affichée une seule fois à la création, stockée uniquement sous forme hachée.
- Portées (scopes) limitées, date d'expiration possible, date de dernière utilisation, révocation immédiate.

**En cas de fuite** : révoquer, remplacer, examiner les journaux. Un secret publié est considéré comme compromis même après purge de l'historique Git.

## 6. API, entrées et protection contre les abus

- Toute entrée est validée par un schéma strict (Pydantic en Python, Zod en TypeScript) : types, longueurs, formats. Les champs inconnus sont refusés.
- Requêtes SQL paramétrées uniquement. Aucune concaténation de texte dans une requête.
- Taille maximale du corps de requête (1 Mo par défaut), délais d'attente (timeouts) et pagination avec maximum (100 éléments).
- **Limitation de débit (rate limiting)**, valeurs par défaut :
  - connexion : 5 par minute et par IP, 10 par 15 minutes et par compte ;
  - réinitialisation de mot de passe : 3 par heure et par compte ;
  - API générale : 100 par minute et par clé ou utilisateur ;
  - réponse `429` avec l'en-tête `Retry-After`, compteur partagé (Redis) dès qu'il y a plusieurs instances.
- CORS : liste blanche explicite d'origines, jamais `*` avec des cookies.
- Protection CSRF sur toute requête qui modifie l'état et s'appuie sur des cookies.
- En-têtes de sécurité : `Content-Security-Policy` stricte, `Strict-Transport-Security`, `X-Content-Type-Options: nosniff`, `Referrer-Policy`, `Permissions-Policy`, `frame-ancestors`.
- Les erreurs suivent un format uniforme, sans trace d'exécution ni détail interne, avec un identifiant de corrélation.
- Toute URL fournie par un utilisateur est validée avant d'être appelée par le serveur (protection SSRF : pas d'adresses internes).
- Les webhooks entrants sont authentifiés par signature, avec tolérance de temps et protection contre le rejeu.
- Les opérations de paiement sont idempotentes.
- La documentation interactive de l'API est désactivée ou protégée en production.

## 7. Fichiers téléversés

- L'autorisation est vérifiée avant la réception du fichier.
- Taille maximale appliquée au proxy et à l'application : 5 Mo pour les images, 10 Mo pour les documents. Nombre de fichiers par requête limité, quota par compte.
- Types autorisés par liste blanche : JPEG, PNG, WebP et PDF par défaut. Tout autre type fait l'objet d'une décision écrite.
- L'extension, le type MIME déclaré et la signature réelle du fichier (magic bytes) doivent concorder.
- Interdits : exécutables, scripts, HTML, archives sans besoin explicite et analyse, SVG non assaini.
- Le fichier est renommé avec un identifiant aléatoire. Le nom d'origine n'est qu'une métadonnée, toujours échappée à l'affichage.
- Stockage privé, hors de la racine web ou dans un bucket privé. L'accès passe par des URL signées de 15 minutes maximum, délivrées après vérification des droits.
- Les images sont réencodées (ce qui supprime les métadonnées et les contenus piégés) et leurs dimensions limitées (6000 pixels par défaut).
- Analyse antivirus (ClamAV) pour les fichiers venant d'utilisateurs externes. Protection contre les archives qui explosent à la décompression.
- Au téléchargement : type de contenu fixé par le serveur, `Content-Disposition` explicite, `nosniff`.

## 8. Base de données

**Structure**
- PostgreSQL. Migrations versionnées. Noms en `snake_case`, tables au pluriel, dates en UTC, identifiants UUID.
- Contraintes dans la base : `NOT NULL`, `UNIQUE`, `CHECK`, clés étrangères. Le code ne suffit pas.
- `organization_id` obligatoire, indexé et relié par clé étrangère sur toute table qui contient des données d'organisation.

**RLS (Row-Level Security)**
- Activée (`ENABLE` et `FORCE`) sur toute table qui contient des données d'organisation ou qui est atteignable depuis l'extérieur.
- Politique par défaut : aucun accès. Une politique par opération (lecture, insertion, modification, suppression).
- Elle est testée par script : un contexte d'organisation A ne voit rien de l'organisation B.
- L'application se connecte avec un rôle sans `BYPASSRLS`, et jamais avec le rôle propriétaire des tables.
- Avec Supabase : aucune table du schéma exposé sans RLS, et la clé `service_role` jamais utilisée pour contourner la RLS dans une requête d'utilisateur.

**Comptes** : un compte applicatif (droits de lecture et d'écriture sur les données seulement), un compte de migration (modification de structure), un compte en lecture seule pour l'analyse. Jamais le super-utilisateur.

**Performance**
- Index sur les clés étrangères et sur les colonnes de filtre et de tri fréquentes (par exemple `organization_id` puis date). Chaque index est justifié par un `EXPLAIN ANALYZE`, et on évite d'en ajouter sans raison car ils ralentissent l'écriture.
- Interdits dans le code applicatif : `SELECT *`, les requêtes sans limite, les boucles de requêtes (N+1).
- Pagination par curseur sur les grandes tables. Partitionnement par date pour les tables d'événements, avec durée de conservation et purge automatique.
- Pool de connexions et délai maximal par requête.

**Données**
- Minimisation : on ne stocke que ce qui sert, avec une durée de conservation écrite.
- Suppression logique quand l'historique est nécessaire, suppression physique planifiée sinon. L'effacement d'un compte reste possible.
- Le journal d'audit est en ajout seul : les droits de modification et de suppression sont retirés.
- Connexions chiffrées (TLS) obligatoires. Les données très sensibles sont chiffrées aussi au niveau de l'application.

## 9. Interface et expérience

- Une vue ne reçoit que les données que le rôle de l'utilisateur permet de voir.
- Chaque vue de données prévoit quatre états : chargement (squelette qui reprend la forme du contenu, pas de roue plein écran), vide (message utile et action proposée), erreur (message clair et bouton pour réessayer), session expirée (reconnexion sans perdre la saisie).
- Une barrière d'erreur globale (error boundary) empêche tout écran blanc : message sobre, identifiant d'erreur, retour possible.
- Les pages 404, 403, 500 et maintenance sont conçues et cohérentes avec la charte graphique.
- Aucune donnée sensible dans l'URL, le `localStorage` ou le `sessionStorage`.
- Pas de `dangerouslySetInnerHTML` ni d'équivalent sans assainissement (DOMPurify). Les liens externes portent `rel="noopener noreferrer"`.
- La validation côté navigateur sert le confort. La sécurité repose sur la validation côté serveur. Les boutons d'envoi sont désactivés pendant la requête.
- Accessibilité : contraste conforme WCAG AA, navigation au clavier, libellés de champs, focus visible. Aucune information portée par la couleur seule : une gravité s'exprime par une couleur, un libellé et une forme.
- Performance, valeurs par défaut : affichage du contenu principal en moins de 2,5 secondes sur une connexion moyenne, JavaScript initial sous 200 Ko compressé, code découpé par page, images en WebP ou AVIF avec dimensions fixées, deux familles de polices au maximum, aucune bibliothèque lourde pour une fonction mineure.
- La charte graphique du projet est écrite dans `docs/charte.md`.

## 10. Pages légales et vie privée

- Politique de confidentialité, conditions d'utilisation et mentions légales, accessibles depuis le pied de page et avant toute inscription. Politique de cookies si des cookies non essentiels sont utilisés.
- La politique de confidentialité indique : les données collectées, la finalité, la base légale, la durée de conservation, les sous-traitants (hébergeur, base de données, email, paiement), les transferts hors du pays, les droits des personnes (accès, rectification, suppression) et un contact.
- Quand un consentement est requis, la case n'est pas précochée. Chaque email marketing contient un lien de désinscription.
- Export et suppression du compte disponibles en libre-service.
- Fichier `/.well-known/security.txt` avec un contact pour signaler une vulnérabilité, et une politique de divulgation responsable.
- Avant tout lancement commercial : relecture par un juriste, et vérification de la loi ivoirienne sur la protection des données personnelles (autorité ARTCI) ainsi que du RGPD si des clients sont en Europe.

## 11. Journalisation et supervision

- Journaux structurés (JSON), niveaux de gravité, identifiant de corrélation par requête.
- Interdits dans les journaux : mots de passe, jetons, clés, numéros de carte, contenus complets de requêtes sensibles.
- Un journal d'audit distinct enregistre les actions sensibles : qui, quoi, quand, depuis où, sur quelle ressource.
- Contrôle de santé (health check), suivi des erreurs (Sentry), alertes sur les pics d'erreurs, d'échecs de connexion et de limites atteintes.
- Durée de conservation des journaux définie. Accès en lecture restreint.

## 12. Dépendances

- Le fichier de verrouillage (lockfile) est versionné, les versions de production sont épinglées.
- Ajouter une dépendance demande : un besoin réel, une maintenance active, une licence compatible, une taille raisonnable, et la vérification du nom exact du paquet (risque de faux paquets aux noms proches).
- Audit à chaque intégration continue (`pip-audit`, `npm audit`) et mises à jour automatiques (Dependabot ou équivalent). Les correctifs critiques sont appliqués sous 7 jours.
- Images Docker : version fixée, utilisateur non root, image minimale.

## 13. Tests et qualité du code

- Typage strict (mypy, TypeScript `strict`), vérification de style et formatage automatiques (Ruff, ESLint, Prettier).
- Tests unitaires et d'intégration, plus des tests de permissions et d'isolation : un utilisateur d'une organisation ne lit, ne modifie et ne supprime rien d'une autre.
- Couverture minimale de 80 % sur l'authentification, les permissions, les paiements et la détection.
- Chaque bug corrigé reçoit un test de non-régression.
- Relecture avant fusion. Seul, on fait une auto-relecture avec la checklist de la section 22.
- Fonctions courtes, noms clairs, pas de code mort.
- Sécurité : analyse statique (Bandit pour Python, règles de sécurité ESLint), scan de dépendances, scan de secrets, et un test d'intrusion avant toute ouverture publique (OWASP ZAP au minimum).
- Les données de test sont synthétiques. Aucune donnée réelle hors production.

## 14. Git et GitHub

- Dépôt privé par défaut. Il devient public seulement après un scan de secrets et une relecture.
- Un push au moins à chaque étape validée et à la fin de chaque session de travail. Commits petits, au format `type(portée): description` (par exemple `feat(auth): ajout du TOTP`).
- Branche `main` protégée : pas de push direct, passage par une pull request avec intégration continue au vert.
- Une branche par fonctionnalité (`feat/...`, `fix/...`).
- Double authentification activée sur le compte GitHub. Clés SSH et jetons d'accès limités en portée et avec expiration.
- `.gitignore` complet dès le départ : environnement, dépendances, builds, fichiers d'éditeur, sauvegardes.
- Pas de gros fichiers binaires ni de copies de base de données dans le dépôt.
- Versions marquées par des tags (`v0.1.0`) et un `CHANGELOG.md`.
- Le `README.md` décrit : le but, l'installation, les variables d'environnement, les commandes, l'architecture et les points de sécurité.

## 15. Environnements et déploiement

- Trois environnements : local, test, production. Données et secrets distincts. Aucune donnée réelle hors production.
- HTTPS partout, redirection automatique du HTTP, HSTS.
- Déploiement automatisé par l'intégration continue. Toute migration est précédée d'une sauvegarde, avec une procédure de retour arrière écrite.
- Les variables d'environnement sont validées au démarrage : l'application refuse de démarrer si une valeur manque.
- Mode debug désactivé en production.
- Envoi d'emails : SPF, DKIM et DMARC configurés sur le domaine.
- Exposition minimale : ports fermés par défaut, base de données non publique quand c'est possible.
- Surveillance de la disponibilité et procédure de déploiement documentée.
- Offres gratuites : on note leurs limites (mise en veille, stockage, historique réduit) et on n'y héberge pas les données réelles d'un client.

## 16. Sauvegardes et reprise

- Sauvegardes automatiques, quotidiennes au minimum, chiffrées, avec une copie chez un autre fournisseur que la base principale. Conservation de 30 jours par défaut.
- L'historique de restauration d'un fournisseur n'est pas une sauvegarde. Certaines offres gratuites ne gardent que quelques heures d'historique : on planifie alors nos propres exports (`pg_dump`).
- Les fichiers téléversés sont sauvegardés aussi.
- Un test de restauration par mois, documenté, avec deux objectifs écrits : perte de données maximale acceptable (RPO) et durée maximale de reprise (RTO).
- Les sauvegardes sont soumises aux mêmes règles d'accès que la production.

## 17. Paiements et abonnements

- Aucune donnée de carte ne passe par nos serveurs ni n'est stockée chez nous : tout transite par la page ou le composant du prestataire.
- Montants, devises et plans sont calculés côté serveur uniquement.
- Webhooks : signature vérifiée, traitement idempotent, journalisation.
- L'état d'un abonnement est enregistré en base à partir de webhooks vérifiés, jamais à partir d'une redirection du navigateur.
- Le prestataire de paiement se branche derrière une interface commune (`PaymentProvider`). Le mode simulation est une implémentation séparée, activée par variable d'environnement, et un test automatique garantit qu'elle ne peut pas être activée en production.
- Les limites de chaque plan et les périodes d'essai sont appliquées côté serveur.
- Les échecs de paiement, relances, annulations, remboursements et factures sont prévus dès la conception.

## 18. Notifications

- Les canaux (email, WhatsApp, autres) passent derrière une interface commune.
- Le contenu d'une notification est minimal : aucune donnée sensible, un lien vers le tableau de bord qui exige une connexion.
- Consentement et désinscription pour chaque canal. Adresse et numéro vérifiés par un code avant tout envoi.
- Limitation de débit et regroupement des alertes pour éviter l'envoi en rafale.
- WhatsApp : modèles de messages approuvés, numéro d'entreprise vérifié, respect des règles de la plateforme.
- Tout texte venant de journaux ou d'utilisateurs est échappé avant d'être inséré dans un message.

## 19. Intelligence artificielle

- L'IA propose, une règle déterministe ou une personne décide pour toute action qui a un effet (blocage, suppression, paiement).
- Ce que l'IA reçoit (journaux, textes d'utilisateurs) est traité comme hostile, car il peut contenir des instructions cachées (injection de prompt). Instructions et données sont séparées, et le modèle n'a accès à aucun outil ni droit dont il n'a pas besoin.
- Les sorties sont validées par un schéma avant usage, jamais exécutées ni insérées sans échappement.
- Données envoyées à un service externe : minimisées et masquées (IP, emails, jetons). Une option de modèle local est prévue pour les clients exigeants.
- Plafond de coût et de débit. Si le service est indisponible, le système continue avec les règles seules.
- Avant mise en production : jeu de données de test, mesure des faux positifs et des faux négatifs, modèles versionnés, décisions et scores journalisés.
- Chaque alerte produite par l'IA affiche sa raison en langage clair.

## 20. Multi-tenant et démonstration

- Toute donnée appartient à une organisation. Aucune requête ne s'exécute sans contexte d'organisation.
- Les quotas et limites par plan sont appliqués côté serveur.
- **Démonstration** : organisation dédiée, données synthétiques générées, accès en lecture seule, aucune action réelle (pas de vrai envoi de notification), débit limité, réinitialisation régulière. Aucun lien possible entre la démo et les données d'un vrai client, aucun vrai nom ni vraie adresse IP.
- Tests d'isolation entre organisations à chaque version.
- Supprimer une organisation supprime toutes ses données, sauvegardes comprises après leur durée de conservation.

## 21. Incident de sécurité

1. Contenir : révoquer les clés et les sessions concernées, couper l'accès touché.
2. Conserver les preuves (journaux) avant tout nettoyage.
3. Évaluer : ce qui a été exposé, depuis quand, pour qui.
4. Corriger la cause, pas seulement le symptôme.
5. Informer les personnes concernées et l'autorité compétente si la loi l'exige.
6. Rédiger un post-mortem sans recherche de coupable, et ajouter un test ou une règle pour que cela ne se reproduise pas.

## 22. Checklists

**Avant chaque commit**
- Aucun secret dans les fichiers modifiés.
- Les tests, le lint et le typage passent.
- Le message de commit est clair.

**Avant chaque fusion**
- Chaque nouvelle route a ses contrôles de permission et son test d'isolation.
- Les entrées sont validées, les réponses ne contiennent que le nécessaire.
- Les états de chargement, vide et erreur existent.
- Toute nouvelle table a `organization_id`, des index justifiés et la RLS activée.
- La migration est réversible, la documentation est à jour.

**Avant chaque mise en production**
- Sauvegarde faite et restauration testée récemment.
- Variables d'environnement vérifiées, debug désactivé.
- HTTPS, HSTS et en-têtes de sécurité actifs, limitation de débit active.
- Scan de dépendances et de secrets propre, test d'intrusion de base effectué.
- Pages 404 et 500 testées, plan de retour arrière prêt.

**Au démarrage d'un nouveau projet**
- Copier ce fichier, créer le dépôt privé, le `.gitignore`, le `.env.example`.
- Installer gitleaks et configurer l'intégration continue.
- Écrire la charte (`docs/charte.md`) et la matrice des permissions (`docs/permissions.md`).
- Prévoir `organization_id` dans le modèle de données.
- Préparer les squelettes de la politique de confidentialité et des conditions d'utilisation.

## 23. Glossaire

- **Argon2id** : algorithme de hachage de mots de passe, volontairement lent pour décourager les attaques par essais.
- **Barrière d'erreur (error boundary)** : mécanisme de l'interface qui attrape une erreur et affiche un message à la place d'un écran blanc.
- **CORS** : règle du navigateur qui décide quels sites peuvent appeler une API.
- **CSP** : en-tête qui limite les sources de scripts et de ressources qu'une page peut charger.
- **CSRF** : attaque qui pousse un utilisateur connecté à effectuer une action à son insu.
- **HSTS** : en-tête qui oblige le navigateur à n'utiliser que HTTPS pour un site.
- **Idempotence** : une opération répétée plusieurs fois a le même effet qu'une seule fois.
- **IDOR** : faille qui permet d'accéder à l'objet d'un autre en changeant un identifiant.
- **JWT** : jeton signé qui porte l'identité d'un utilisateur.
- **k-anonymat (mots de passe)** : méthode qui vérifie un mot de passe contre une liste de fuites sans envoyer le mot de passe complet.
- **Magic bytes** : premiers octets d'un fichier qui révèlent son vrai type.
- **MFA / 2FA / TOTP** : authentification à plusieurs facteurs, avec un code temporaire généré par une application.
- **RLS** : Row-Level Security, filtre appliqué par la base de données elle-même, ligne par ligne.
- **RPO / RTO** : perte de données maximale acceptable, et durée maximale de reprise après un incident.
- **Rate limiting** : limitation du nombre de requêtes autorisées sur une période.
- **SSRF** : attaque qui pousse le serveur à appeler une adresse interne ou choisie par l'attaquant.
- **Tenant** : organisation cliente d'un service partagé, isolée des autres.
- **Webhook** : appel automatique envoyé par un service externe à notre serveur quand un événement se produit.
- **XSS** : injection de script dans une page vue par d'autres utilisateurs.
