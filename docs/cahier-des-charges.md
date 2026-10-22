Cahier des charges V1 : outil de surveillance de sécurité pour sites web
Auteur : Dimitri Nelson Baliguini Demba. Version 0.2, brouillon à valider.
1. Contexte et objectif
Les petites et moyennes structures n'ont ni équipe de sécurité ni budget pour les grandes plateformes (Splunk, Microsoft Sentinel, Tenable). Les outils gratuits comme Wazuh sont puissants mais lourds à installer et à maîtriser. Ce projet vise à construire, par versions successives, un outil qui détecte et signale les tentatives d'attaque contre un site web, puis les failles de ce site, avant d'évoluer vers une version multi-clients et une version entreprise installable chez le client.
Ce projet est aussi une formation : chaque étape inclut l'apprentissage des notions de cybersécurité utilisées.
Objectif de la V1a : brancher un site web sur l'outil, détecter les tentatives d'attaque courantes à partir des événements de sécurité qu'il envoie, les afficher dans un tableau de bord et envoyer des alertes par email.
Objectif de la V1b : ajouter la coque SaaS (comptes, plans, paiement simulé, démonstration), les notifications WhatsApp et une première couche de détection par intelligence artificielle.
2. Périmètre de la V1
V1a : le cœur de l'outil
• Une installation, un seul propriétaire de données, un site surveillé. Le modèle de données prévoit déjà plusieurs sites et plusieurs organisations.
• Collecte par SDK : un petit morceau de code intégré au site envoie ses événements de sécurité à l'API. Le site de test est le portfolio de Dimitri, hébergé sur Vercel, qui ne donne pas accès aux fichiers de logs.
• Huit règles de détection (section 4), alertes par email, tableau de bord, journal d'audit.
• Sécurité complète de l'outil (section 5) : RLS, limitation de débit, secrets protégés, sauvegardes automatiques.
• Écrans de chargement, d'erreur, pages 404, politique de confidentialité, installation par Docker Compose.
V1b : la coque SaaS et l'intelligence artificielle
• Comptes, organisations, plans d'abonnement et paiement simulé derrière une interface commune.
• Démonstration en lecture seule avec données synthétiques, qui mène à l'inscription puis au paiement simulé.
• Notifications WhatsApp en plus de l'email.
• Détection par IA : anomalies en mode fantôme, puis explication des alertes en langage clair sur des données masquées.
• Collecteur de logs en option, pour les serveurs classiques (Apache, Nginx).
Exclu des V1a et V1b
• Blocage automatique des IP.
• Scan de failles et plusieurs sites par organisation (V2).
• Clé de chiffrement distincte par tenant et paiement réel (V3).
• Agents sur les serveurs et systèmes internes (V4).
3. Utilisateurs
• Propriétaire : crée l'organisation, gère le plan, la facturation et les clés API.
• Administrateur : déclare le site, règle les alertes, consulte tout.
• Membre : traite les alertes et consulte le tableau de bord.
• Lecteur : consultation seule.
• Visiteur de démonstration : accès en lecture seule à une organisation fictive, sans compte.
4. Fonctionnalités de la V1
V1a
• F1. Authentification : connexion sécurisée, double authentification (TOTP) pour les administrateurs, réinitialisation par lien à usage unique, sessions visibles et révocables.
• F2. Gestion du site : nom, domaine, clé API propre au site (affichée une seule fois, stockée hachée), révocation.
• F3. Collecte : le SDK intégré au site envoie des lots d'événements à l'API en HTTPS, signés avec la clé API. Pour le portfolio, il reprend les événements déjà enregistrés (connexion échouée, limite de fréquence, honeypot) et y ajoute les requêtes suspectes.
• F4. Normalisation et stockage : chaque événement est découpé en champs (date, IP, méthode, chemin, paramètres, code de réponse, user-agent) et enregistré. Les données sensibles dans les URL (jetons, mots de passe) sont masquées avant stockage.
• F5. Moteur de détection : applique les règles ci-dessous à chaque nouvel événement.
• F6. Alertes par email : regroupement par IP et par règle sur 15 minutes pour éviter les doublons, seuil de gravité minimum configurable. L'email indique la règle, l'IP, l'horaire, un extrait masqué et une recommandation.
• F7. Tableau de bord : événements et alertes par jour, alertes par gravité, top des IP et des règles, liste filtrable des alertes avec statut (nouveau, vu, traité, faux positif).
• F8. Journal d'audit : trace des connexions, changements de configuration et actions sur les alertes.
V1b
• F9. Comptes et organisations : inscription, vérification de l'email, rôles.
• F10. Plans et abonnements simulés : limites par plan appliquées côté serveur, paiement simulé derrière une interface commune (PaymentProvider), impossible à activer en production.
• F11. Démonstration : organisation fictive en lecture seule, données synthétiques, parcours vers l'inscription et le paiement.
• F12. Notifications WhatsApp : numéro vérifié par code, consentement, messages minimaux avec lien vers le tableau de bord.
• F13. Détection par IA : scores d'anomalie par IP et par fenêtre de temps, affichés sans déclencher d'alerte tant que les données sont rares (mode fantôme), puis explication des alertes en langage clair.
Règles de détection de la V1
Code
Ce que la règle repère
Gravité
R1
Accès à des chemins sensibles (/.env, /.git, /phpmyadmin, /wp-admin, fichiers .sql)
Moyenne
R2
Rafale d'erreurs 404 depuis une même IP (scan de chemins)
Moyenne
R3
Motifs d'injection SQL dans l'URL ou les paramètres
Élevée
R4
Motifs XSS (balises script, attributs onerror)
Élevée
R5
Traversée de répertoires (../, %2e%2e, /etc/passwd)
Élevée
R6
User-agent d'outil d'attaque connu (sqlmap, Nikto, Nuclei, Burp)
Moyenne
R7
Brute force : échecs répétés sur la page de connexion configurée
Élevée
R8
Cadence anormale : trop de requêtes par minute depuis une IP
Faible à moyenne
Les seuils de chaque règle sont modifiables dans l'interface. La corrélation entre plusieurs règles (par exemple un scan suivi d'une connexion réussie) est prévue pour une version ultérieure.
5. Exigences non fonctionnelles
5.1 Sécurité de l'outil
Un outil de sécurité vulnérable est pire que pas d'outil. Il doit donc être au niveau qu'il prétend contrôler. Les règles détaillées sont dans le fichier REGLES-PROJET.md, qui s'applique à ce projet comme à tous les suivants.
• Mots de passe hachés avec Argon2id, 12 caractères minimum, refus des mots de passe compromis. Double authentification (TOTP) obligatoire pour les administrateurs.
• Droits vérifiés côté serveur à chaque requête, y compris l'appartenance de l'objet à l'organisation. L'interface masque, le serveur décide.
• RLS activée sur toutes les tables de données et testée par script. L'application se connecte avec un rôle qui ne peut pas la contourner.
• Requêtes SQL préparées, sorties échappées, jetons CSRF, en-têtes de sécurité (CSP, HSTS), CORS en liste blanche.
• Limitation de débit sur la connexion, la réinitialisation de mot de passe, l'API et l'ingestion.
• Clés API stockées hachées, affichées une seule fois, avec portée et révocation. Secrets hors du code, scan automatique de secrets (gitleaks). Seules les clés publiques côté navigateur.
• Téléversements : types autorisés par liste blanche et vérifiés sur la signature réelle du fichier, taille maximale (5 Mo pour les images, 10 Mo pour les documents), stockage privé, URL signées.
• Les données reçues (événements, textes traités par l'IA) sont considérées comme hostiles et validées par schéma.
• Journal d'audit en ajout seul, sauvegardes automatiques chiffrées avec test de restauration mensuel.
5.2 Qualité du code
• Architecture en couches. Backend Python typé (mypy), formatage et analyse avec Ruff. Frontend TypeScript strict avec ESLint et Prettier.
• Tests : pytest et Vitest, tests de permissions et d'isolation entre organisations, chaque règle de détection testée avec des attaques et du trafic normal. Couverture minimale de 80 % sur l'authentification, les permissions, la détection et le paiement.
• Git sur GitHub : une branche par fonctionnalité, branche principale protégée, intégration continue GitHub Actions, push régulier à chaque étape validée.
• Migrations versionnées (Alembic), README et documentation tenus à jour.
• Écrans de chargement, d'erreur et pages 404 et 500 conçus, barrière d'erreur globale : jamais d'écran blanc.
5.3 Base de données
• Identifiants UUID, dates en UTC, contraintes dans la base, organization_id obligatoire et indexé sur toute table de données.
• Index sur la date, l'IP, le site et l'organisation, justifiés par EXPLAIN ANALYZE. Pas de SELECT *, pagination par curseur.
• Conservation : 7 à 14 jours pour les événements bruts pendant le MVP gratuit (stockage limité), 12 mois pour les alertes, avec purge automatique.
• Exports automatiques quotidiens vers un stockage privé, car l'historique de restauration de l'offre gratuite ne dure que quelques heures. Test de restauration mensuel.
5.4 Scalabilité et performance
• La V1a vise un site de trafic modeste. L'objectif est de ne pas bloquer l'évolution, pas d'optimiser trop tôt.
• Insertion des événements par lots. L'ingestion est écrite derrière une interface pour brancher plus tard une file d'attente (Redis) sans réécrire le reste.
• Tables d'événements partitionnées par mois si le volume grandit.
• Interface rapide et légère : contenu principal affiché en moins de 2,5 secondes, JavaScript initial sous 200 Ko compressé, code découpé par page, images optimisées.
5.5 Confidentialité et conformité
• Les adresses IP sont des données personnelles dans beaucoup de législations : minimisation, durée de conservation documentée, suppression possible. Export et suppression de compte en libre-service.
• Politique de confidentialité, conditions d'utilisation et mentions légales accessibles avant l'inscription, relues par un juriste avant toute commercialisation. Vérification de la loi ivoirienne sur la protection des données personnelles (autorité ARTCI).
• Aucune télémétrie. Les données envoyées à un service d'IA externe sont minimisées et masquées, avec une option de modèle local prévue pour les clients exigeants.
5.6 Exploitation
• Docker Compose en local. Test en ligne sur des offres gratuites (Neon pour la base de données, hébergement de test à choisir), en notant leurs limites de mise en veille et de stockage.
• Journaux de l'outil lui-même, contrôle de santé, suivi des erreurs, procédure de mise à jour.
6. Architecture proposée (V1)
1. Le site intègre le SDK, qui capture les événements de sécurité et les requêtes suspectes.
2. Le SDK envoie des lots d'événements à l'API d'ingestion avec la clé API du site.
3. L'API vérifie la clé, valide et normalise les données, puis les enregistre dans PostgreSQL.
4. Le moteur de règles analyse les nouveaux événements et crée ou met à jour les alertes. En V1b, la couche d'IA calcule en parallèle ses scores, d'abord en mode fantôme.
5. Le module de notifications envoie les emails (V1a) et les messages WhatsApp (V1b). Le tableau de bord React lit les alertes et les statistiques par l'API.
7. Modèle de données préliminaire
• organizations : id (UUID), nom, plan, indicateur de démonstration, date de création.
• users : id, organization_id, email, mot de passe haché, rôle, secret TOTP chiffré, dernière connexion.
• sites : id, organization_id, nom, domaine, date de vérification de propriété, date de création.
• api_keys : id, site_id, préfixe, empreinte de la clé, portées, expiration, dernière utilisation, date de révocation.
• log_events : id, organization_id, site_id, date, IP, méthode, chemin, paramètres masqués, code de réponse, user-agent, source (SDK ou collecteur).
• rules : id, code, nom, gravité, activée, configuration (seuils).
• alerts : id, organization_id, site_id, rule_id ou origine IA, gravité, IP, première et dernière occurrence, nombre d'occurrences, statut, explication, contexte.
• notifications : id, alert_id, canal (email ou WhatsApp), date d'envoi, résultat.
• notification_channels (V1b) : id, organization_id, canal, adresse ou numéro, date de vérification, consentement.
• plans (V1b) : id, nom, limites (sites, événements par mois, canaux).
• subscriptions (V1b) : id, organization_id, plan_id, statut, période, fournisseur (simulation), identifiant externe.
• payment_events (V1b) : id, subscription_id, type, montant calculé côté serveur, clé d'idempotence, date.
• anomaly_scores (V1b) : id, organization_id, site_id, fenêtre de temps, IP, score, modèle et version.
• audit_log : id, organization_id, user_id, action, IP, date, détails.
8. Choix techniques à valider
Domaine
Choix retenu
Alternative
Backend et moteur de règles
Python avec FastAPI et schémas Pydantic
Node.js avec NestJS
Base de données
PostgreSQL chez Neon (offre gratuite pour le MVP), RLS activée
Supabase (500 Mo et pause après 7 jours d'inactivité sur l'offre gratuite)
Migrations
Alembic
SQL versionné à la main
Frontend
React, TypeScript, Vite, Tailwind, selon une charte graphique sobre
Next.js
Collecte
SDK intégré au site (portfolio d'abord)
Collecteur de logs, ou Log Drains de Vercel (offres payantes)
IA
scikit-learn (Isolation Forest) en mode fantôme, puis explication des alertes par un modèle de langage sur données masquées
Modèle local
Notifications
Email par SMTP (Brevo ou Resend), WhatsApp par l'API Cloud de Meta
Telegram pour les essais
Paiement
Interface PaymentProvider avec fournisseur simulé
CinetPay, PayDunya ou Flutterwave, à étudier plus tard
Déploiement et qualité
Docker Compose, GitHub Actions, pytest, Ruff, mypy, Vitest, ESLint, gitleaks
Hébergement gratuit de test à choisir
9. Feuille de route
V1a, étape par étape. Chaque étape a un livrable, des tests et une validation avant de passer à la suivante.
1. Cadrage : ce document validé, REGLES-PROJET.md adopté.
2. Charte graphique définie avec Dimitri avant toute interface. Bases de sécurité web et laboratoire local (OWASP Juice Shop, DVWA) pour produire de vrais logs d'attaque.
3. Fondations : dépôt GitHub privé, Docker Compose, intégration continue, migrations, base Neon avec RLS, authentification sécurisée.
4. Ingestion : API, SDK, normalisation, stockage.
5. Moteur de règles R1 à R8, avec tests pour chaque règle.
6. Alertes par email avec regroupement.
7. Tableau de bord avec états de chargement, d'erreur et page 404.
8. Durcissement : tests d'intrusion sur l'outil lui-même, revue du code, corrections.
9. Branchement sur le portfolio et réglage des faux positifs.
V1b
1. Comptes, organisations, rôles, plans et abonnements simulés.
2. Démonstration avec données synthétiques et parcours vers le paiement simulé.
3. Notifications WhatsApp.
4. IA en mode fantôme, puis explication des alertes.
5. Pages légales, test d'intrusion de la coque SaaS, dossier de confiance (politique de sécurité écrite, rapport de test d'intrusion) pour les clients exigeants comme les banques.
Versions suivantes
• V2 : plusieurs sites par organisation, vérification de propriété du domaine, scan de failles avec ZAP ou Nuclei, suivi des corrections, blocage d'IP optionnel.
• V3 : clé de chiffrement par tenant, coffre de clés, paiement réel via un agrégateur.
• V4 : version entreprise auto-hébergée, agents sur les serveurs, systèmes internes, rapports de conformité, intégration éventuelle de Wazuh ou DefectDojo.
10. Risques
• Faux positifs (alertes sur un trafic légitime) : seuils réglables, statut « faux positif », essais sur le laboratoire et sur le portfolio.
• Peu de données pour l'IA : le portfolio reçoit peu de trafic. Mode fantôme et attaques simulées dans un laboratoire local.
• Limites des offres gratuites (stockage, mise en veille, historique court) : conservation courte, purge, exports automatiques.
• Sécurité de l'outil : étape de durcissement dédiée, tests d'intrusion sur lui-même, application de REGLES-PROJET.md.
• Données personnelles : minimisation, conservation limitée, relecture juridique avant commercialisation.
• Injection dans les données traitées par l'IA : les événements sont traités comme hostiles. L'IA propose, une règle ou une personne décide.
• Scan non autorisé (V2) : vérification de propriété du domaine obligatoire avant tout scan.
• Charge de travail : découpage en V1a et V1b, périmètre de chaque étape gelé après validation.
• Crédibilité auprès des banques : elles demandent des preuves (test d'intrusion indépendant, politiques écrites, hébergement documenté), à préparer dès la V1b.
11. Décisions en attente
1. Découpage en V1a et V1b : accepté.
2. Stack : validé (section 8). Base de données : Neon recommandé face à Supabase, à confirmer.
3. Mode de collecte : SDK pour le portfolio, car Vercel ne propose les Log Drains que sur ses offres payantes. Collecteur de logs en option plus tard.
4. Charte graphique : à définir ensemble (public visé, références, ton, couleurs, typographie).
5. Site d'essai : le portfolio de Dimitri.
6. Durées de conservation : 7 à 14 jours pour les événements bruts pendant le MVP, 12 mois pour les alertes.
7. Hébergement gratuit de test pour l'API et l'interface : à choisir.
8. Nom du projet : Guetteur. Vérification de la disponibilité (domaine, GitHub, recherche web, marque à l'OAPI) encore à faire.
12. Glossaire
• API : interface par laquelle deux programmes échangent des données.
• Brute force : essais répétés de mots de passe jusqu'à trouver le bon.
• CSRF : attaque qui pousse un utilisateur connecté à effectuer une action à son insu.
• Collecteur : petit programme qui lit les logs d'un serveur et les envoie à l'outil.
• Faux positif : alerte déclenchée par un comportement légitime.
• Injection SQL : insertion de commandes de base de données dans une requête pour lire ou modifier des données.
• Multi-tenant / single-tenant : une installation qui sert plusieurs clients isolés, ou un seul.
• OWASP Top 10 : liste des dix risques de sécurité web les plus courants, publiée par l'organisation OWASP.
• Rate limiting : limitation du nombre de requêtes autorisées sur une période.
• RSSI : Responsable de la Sécurité des Systèmes d'Information, la personne chargée de la sécurité dans une organisation.
• SIEM : outil qui collecte et corrèle les journaux pour produire des alertes.
• SOC : Security Operations Center, équipe qui surveille les alertes de sécurité en continu.
• User-agent : texte envoyé par un navigateur ou un outil pour s'identifier.
• WAF : pare-feu qui filtre les requêtes malveillantes vers un site web.
• XSS : injection de code script dans une page vue par d'autres utilisateurs.
• Isolation Forest : algorithme qui repère les comportements rares en les isolant du reste des données.
• Log Drains : fonction de Vercel qui envoie les logs d'un site vers un service externe, réservée aux offres payantes.
• Mode fantôme : la détection calcule et affiche ses scores sans déclencher d'alerte, le temps de vérifier qu'elle est fiable.
• PaymentProvider : interface commune qui permet de changer de fournisseur de paiement sans réécrire l'application.
• RLS : Row-Level Security, filtre appliqué par la base de données elle-même, ligne par ligne, selon le propriétaire.
• SDK : petit morceau de code fourni pour intégrer l'outil dans un site.
• TOTP : code temporaire à usage unique généré par une application d'authentification.
• Webhook : appel automatique envoyé par un service externe à notre serveur quand un événement se produit.