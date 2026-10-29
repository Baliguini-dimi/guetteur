# Configuration locale

Copiez `.env.example` vers `.env` et renseignez les valeurs adaptées à votre environnement. Les variables secrètes doivent rester hors de Git; les mots de passe intégrés aux URL de base de données sont à générer en hexadécimal sur 48 caractères pour éviter les caractères spéciaux dans l'URL. Docker Compose lit `.env`, tandis que l'application ne lit que les variables d'environnement de son processus.

| Variable | Rôle | Secret (oui ou non) | Valeur locale conseillée |
|---|---|---|---|
| `APP_ENV` | Environnement de l'application | non | `local` |
| `APP_SECRET_KEY` | Clé secrète de l'application | oui | à générer, 64 caractères hexadécimaux |
| `ALLOWED_ORIGINS` | Origines autorisées par CORS | non | `http://localhost:5173` |
| `POSTGRES_ADMIN_PASSWORD` | Mot de passe du compte PostgreSQL administrateur | oui | à générer |
| `APP_DATABASE_PASSWORD` | Mot de passe du compte applicatif PostgreSQL | oui | à générer |
| `MIGRATION_DATABASE_PASSWORD` | Mot de passe du compte PostgreSQL de migration | oui | à générer |
| `GUETTEUR_DB_PORT` | Port local publié par Docker Compose pour PostgreSQL | non | `5432` par défaut; à changer en cas de conflit avec un autre programme |
| `GUETTEUR_API_PORT` | Port local publié par Docker Compose pour l'API | non | `8000` par défaut; à changer en cas de conflit avec un autre programme |
| `SESSION_COOKIE_SECURE` | Active l'attribut Secure des cookies de session | non | `false` en local seulement |
| `SESSION_MAX_AGE_HOURS` | Durée maximale d'une session en heures | non | `12` |
| `ADMIN_SESSION_IDLE_MINUTES` | Expiration d'inactivité des sessions administrateur | non | `30` |
| `DEMO_MODE` | Active le mode démonstration | non | `false` |
| `DATABASE_URL` | Connexion PostgreSQL de l'application | oui | Docker Compose la construit pour l'API; à composer avec les mots de passe pour les commandes hors Docker |
| `DATABASE_MIGRATION_URL` | Connexion PostgreSQL des migrations | oui | à composer avec les mots de passe pour exécuter les migrations |
| `REDIS_URL` | Connexion au service Redis | oui | à définir, inutilisé tant que Redis n'est pas ajouté |
| `RATE_LIMIT_LOGIN_PER_MINUTE_IP` | Connexions par minute et par adresse IP | non | `5` |
| `RATE_LIMIT_LOGIN_PER_15MIN_ACCOUNT` | Connexions par compte sur quinze minutes | non | `10` |
| `RATE_LIMIT_RESET_PER_HOUR_ACCOUNT` | Réinitialisations par compte et par heure | non | `3` |
| `RATE_LIMIT_API_PER_MINUTE` | Requêtes API par minute | non | `100` |
| `UPLOAD_MAX_IMAGE_MB` | Taille maximale des images téléversées | non | `5` |
| `UPLOAD_MAX_DOCUMENT_MB` | Taille maximale des documents téléversés | non | `10` |
| `UPLOAD_STORAGE_PATH` | Répertoire de stockage local des fichiers | non | à définir, dossier privé hors du dépôt |
| `RETENTION_RAW_EVENTS_DAYS` | Conservation des événements bruts en jours | non | `14` |
| `RETENTION_ALERTS_MONTHS` | Conservation des alertes en mois | non | `12` |
| `SMTP_HOST` | Serveur SMTP | non | à définir |
| `SMTP_PORT` | Port du serveur SMTP | non | à définir |
| `SMTP_USER` | Identifiant du compte SMTP | non | à définir |
| `SMTP_PASSWORD` | Mot de passe du compte SMTP | oui | fourni par le fournisseur d'email |
| `MAIL_FROM` | Adresse d'expédition des emails | non | à définir |
| `WHATSAPP_ACCESS_TOKEN` | Jeton d'accès WhatsApp | oui | fourni par Meta |
| `WHATSAPP_PHONE_NUMBER_ID` | Identifiant du numéro WhatsApp | non | à définir |
| `PAYMENT_PROVIDER` | Fournisseur de paiement sélectionné | non | `simulation` hors production uniquement |
| `PAYMENT_WEBHOOK_SECRET` | Secret de signature des webhooks de paiement | oui | à générer en simulation, fourni par le prestataire en réel |
| `AI_ENABLED` | Active les fonctions d'intelligence artificielle | non | `false` |
| `AI_MODE` | Mode de fonctionnement de la détection IA | non | `shadow` |
| `LLM_API_KEY` | Clé d'accès au modèle de langage | oui | fourni par le fournisseur du modèle |
| `LLM_MONTHLY_BUDGET_EUR` | Budget mensuel du modèle de langage en euros | non | à définir |
| `BACKUP_STORAGE_URL` | Emplacement des sauvegardes | oui | à définir |
| `BACKUP_ENCRYPTION_KEY` | Clé de chiffrement des sauvegardes | oui | à générer |
| `VITE_API_URL` | Adresse publique de l'API pour le frontend | non | `http://localhost:8000` |

