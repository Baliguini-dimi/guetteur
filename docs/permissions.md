# Matrice des permissions

La V1a fonctionne en installation à propriétaire unique. Les rôles de membre et lecteur servent de cible de conception pour V1b; ils n'impliquent pas que l'inscription ou le multi-tenant sont livrés en V1a.

| Action | Propriétaire V1a | Administrateur V1b | Membre V1b | Lecteur V1b | Démo |
|---|---:|---:|---:|---:|---:|
| Consulter tableau de bord, événements et alertes | Oui | Oui | Oui | Oui | Oui, données fictives seulement |
| Modifier les règles et seuils | Oui | Oui | Non | Non | Non |
| Modifier les paramètres du site | Oui | Oui | Non | Non | Non |
| Créer ou révoquer une clé API | Oui, nouvelle authentification | Oui, nouvelle authentification | Non | Non | Non |
| Modifier le statut d'une alerte | Oui | Oui | Oui | Non | Non |
| Consulter le journal d'audit | Oui | Oui | Non | Non | Non |
| Gérer membres et organisations | Hors périmètre V1a | Selon politique V1b à définir | Non | Non | Non |
| Paiement ou abonnement | Hors périmètre V1a | Hors périmètre V1a | Non | Non | Non |

## Contrôles obligatoires côté serveur

- La V1a n'autorise que le propriétaire configuré côté serveur; le client ne choisit pas son rôle.
- En V1b, chaque requête vérifie l'identité, l'organisation et le droit sur l'objet. Une ressource d'une autre organisation répond 404.
- La démonstration est isolée, en lecture seule, limitée aux données synthétiques. Aucun envoi réel de notification ni aucune mutation n'est permis.
- Toute nouvelle route doit inclure une vérification d'isolation entre deux organisations.

## Droits en base

| Rôle PostgreSQL | `organizations` | `sites` | `log_events` | `users` | `backup_codes` | `sessions` | `audit_log` | `alembic_version` |
|---|---|---|---|---|---|---|---|---|
| `app_user` | lecture RLS | lecture, insertion, modification, suppression RLS | lecture, insertion RLS | lecture RLS; modification limitée à `password_hash`, `totp_secret_encrypted`, `totp_enabled_at`, `totp_last_step`, `last_login_at` | lecture, insertion, suppression RLS; modification limitée à `used_at` | lecture, insertion RLS; modification limitée à `last_seen_at`, `stage`, `expires_at`, `revoked_at` | lecture et insertion RLS, ajout seul | aucun droit |
| `bootstrap_user` | insertion RLS, identité imposée par le contexte | aucun droit | aucun droit | insertion RLS réservée au rôle `owner` et au contexte courant | aucun droit | aucun droit | insertion RLS dans le contexte courant | aucun droit |
| `migration_user` | propriétaire, contrôle complet de schéma et données | propriétaire, contrôle complet de schéma et données | propriétaire, contrôle complet de schéma et données | propriétaire, contrôle complet de schéma et données | propriétaire, contrôle complet de schéma et données | propriétaire, contrôle complet de schéma et données | propriétaire, contrôle complet de schéma et données | propriétaire, contrôle complet de schéma et données |

Les droits de propriété de `migration_user` résultent de la création des tables par les migrations. Aucun privilège n'est accordé par défaut à `PUBLIC`.
