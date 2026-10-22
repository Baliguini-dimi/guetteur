# Configuration locale

Copiez `.env.example` vers `.env` et renseignez les valeurs adaptées à votre environnement. Les variables secrètes doivent rester hors de Git; les mots de passe intégrés aux URL de base de données sont à générer en hexadécimal sur 48 caractères pour éviter les caractères spéciaux dans l'URL.

| Variable | Rôle | Secret (oui ou non) | Valeur locale conseillée |
|---|---|---|---|
| `APP_ENV` | Environnement de l'application | non | `local` |
| `APP_SECRET_KEY` | Clé secrète de l'application | oui | à générer |
| `ALLOWED_ORIGINS` | Origines autorisées par CORS | non | `http://localhost:5173` |
| `POSTGRES_ADMIN_PASSWORD` | Mot de passe du compte PostgreSQL administrateur | oui | à générer |
| `APP_DATABASE_PASSWORD` | Mot de passe du compte applicatif PostgreSQL | oui | à générer |
| `MIGRATION_DATABASE_PASSWORD` | Mot de passe du compte PostgreSQL de migration | oui | à générer |
| `SESSION_COOKIE_SECURE` | Active l'attribut Secure des cookies de session | non | `false` en local seulement |
| `SESSION_MAX_AGE_HOURS` | Durée maximale d'une session en heures | non | `12` |
| `ADMIN_SESSION_IDLE_MINUTES` | Expiration d'inactivité des sessions administrateur | non | `30` |
| `DEMO_MODE` | Active le mode démonstration | non | à définir |
| `DATABASE_URL` | Connexion PostgreSQL de l'application | oui | à générer |
| `DATABASE_MIGRATION_URL` | Connexion PostgreSQL des migrations | oui | à générer |
| `REDIS_URL` | Connexion au service Redis | oui | à générer |
| `RATE_LIMIT_LOGIN_PER_MINUTE_IP` | Connexions par minute et par adresse IP | non | `5` |
| `RATE_LIMIT_LOGIN_PER_15MIN_ACCOUNT` | Connexions par compte sur quinze minutes | non | `10` |
| `RATE_LIMIT_RESET_PER_HOUR_ACCOUNT` | Réinitialisations par compte et par heure | non | `3` |
| `RATE_LIMIT_API_PER_MINUTE` | Requêtes API par minute | non | `100` |
| `UPLOAD_MAX_IMAGE_MB` | Taille maximale des images téléversées | non | `5` |
| `UPLOAD_MAX_DOCUMENT_MB` | Taille maximale des documents téléversés | non | `10` |
| `UPLOAD_STORAGE_PATH` | Répertoire de stockage local des fichiers | non | à définir |
| `RETENTION_RAW_EVENTS_DAYS` | Conservation des événements bruts en jours | non | `14` |
| `RETENTION_ALERTS_MONTHS` | Conservation des alertes en mois | non | `12` |
| `SMTP_HOST` | Serveur SMTP | non | à définir |
| `SMTP_PORT` | Port du serveur SMTP | non | à définir |
| `SMTP_USER` | Identifiant du compte SMTP | non | à définir |
| `SMTP_PASSWORD` | Mot de passe du compte SMTP | oui | à générer |
| `MAIL_FROM` | Adresse d'expédition des emails | non | à définir |
| `WHATSAPP_ACCESS_TOKEN` | Jeton d'accès WhatsApp | oui | à générer |
| `WHATSAPP_PHONE_NUMBER_ID` | Identifiant du numéro WhatsApp | non | à définir |
| `PAYMENT_PROVIDER` | Fournisseur de paiement sélectionné | non | `simulation` hors production uniquement |
| `PAYMENT_WEBHOOK_SECRET` | Secret de signature des webhooks de paiement | oui | à générer |
| `AI_ENABLED` | Active les fonctions d'intelligence artificielle | non | `false` |
| `AI_MODE` | Mode de fonctionnement de la détection IA | non | `shadow` |
| `LLM_API_KEY` | Clé d'accès au modèle de langage | oui | à générer |
| `LLM_MONTHLY_BUDGET_EUR` | Budget mensuel du modèle de langage en euros | non | à définir |
| `BACKUP_STORAGE_URL` | Emplacement des sauvegardes | oui | à générer |
| `BACKUP_ENCRYPTION_KEY` | Clé de chiffrement des sauvegardes | oui | à générer |
| `VITE_API_URL` | Adresse publique de l'API pour le frontend | non | `http://localhost:8000` |

Les mots de passe des connexions PostgreSQL doivent être générés sous forme hexadécimale sur 48 caractères. Ne réutilisez pas les secrets entre environnements.
