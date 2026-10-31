"""Crée les tables d'authentification avec une isolation PostgreSQL stricte."""

from alembic import op

revision = "0002_auth_tables"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE users (
            id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            organization_id uuid NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
            email varchar(254) NOT NULL,
            password_hash text NOT NULL,
            role varchar(20) NOT NULL,
            totp_secret_encrypted bytea,
            totp_enabled_at timestamptz,
            totp_last_step bigint,
            created_at timestamptz NOT NULL DEFAULT now(),
            last_login_at timestamptz,
            disabled_at timestamptz,
            CONSTRAINT users_email_lowercase CHECK (email = lower(email)),
            CONSTRAINT users_email_unique UNIQUE (email),
            CONSTRAINT users_role_valid CHECK (role IN ('owner', 'admin', 'member', 'viewer')),
            CONSTRAINT users_id_organization_id_unique UNIQUE (id, organization_id)
        )
        """
    )
    op.execute(
        """
        CREATE TABLE backup_codes (
            id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            organization_id uuid NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
            user_id uuid NOT NULL,
            code_hash text NOT NULL,
            used_at timestamptz,
            created_at timestamptz NOT NULL DEFAULT now(),
            CONSTRAINT backup_codes_user_organization_fk
                FOREIGN KEY (user_id, organization_id)
                REFERENCES users (id, organization_id) ON DELETE CASCADE
        )
        """
    )
    op.execute(
        """
        CREATE TABLE sessions (
            id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            organization_id uuid NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
            user_id uuid NOT NULL,
            secret_hash bytea NOT NULL,
            stage varchar(12) NOT NULL,
            created_at timestamptz NOT NULL DEFAULT now(),
            last_seen_at timestamptz,
            expires_at timestamptz NOT NULL,
            revoked_at timestamptz,
            user_agent_hash bytea,
            CONSTRAINT sessions_stage_valid CHECK (stage IN ('provisional', 'full')),
            CONSTRAINT sessions_user_organization_fk
                FOREIGN KEY (user_id, organization_id)
                REFERENCES users (id, organization_id) ON DELETE CASCADE,
            CONSTRAINT sessions_organization_secret_unique UNIQUE (organization_id, secret_hash)
        )
        """
    )
    op.execute("CREATE INDEX sessions_organization_user_idx ON sessions (organization_id, user_id)")
    op.execute("CREATE INDEX sessions_expires_at_idx ON sessions (expires_at)")
    op.execute(
        """
        CREATE TABLE audit_log (
            id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            organization_id uuid NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
            user_id uuid,
            action varchar(64) NOT NULL,
            outcome varchar(16) NOT NULL,
            ip inet,
            details jsonb NOT NULL DEFAULT '{}'::jsonb,
            occurred_at timestamptz NOT NULL DEFAULT now(),
            CONSTRAINT audit_log_outcome_valid CHECK (outcome IN ('success', 'failure'))
        )
        """
    )
    op.execute(
        "CREATE INDEX audit_log_organization_time_idx "
        "ON audit_log (organization_id, occurred_at DESC)"
    )

    for table in ("users", "backup_codes", "sessions", "audit_log"):
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
        op.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY")
        op.execute(f"REVOKE ALL ON TABLE {table} FROM PUBLIC")
        op.execute(
            f"""
            CREATE POLICY {table}_select ON {table}
            FOR SELECT TO app_user
            USING (organization_id = nullif(current_setting('app.organization_id', true), '')::uuid)
            """
        )

    op.execute(
        """
        CREATE POLICY users_update ON users
        FOR UPDATE TO app_user
        USING (organization_id = nullif(current_setting('app.organization_id', true), '')::uuid)
        WITH CHECK (
            organization_id = nullif(current_setting('app.organization_id', true), '')::uuid
        )
        """
    )
    op.execute(
        """
        CREATE POLICY users_bootstrap_insert ON users
        FOR INSERT TO bootstrap_user
        WITH CHECK (
            role = 'owner'
            AND organization_id = nullif(current_setting('app.organization_id', true), '')::uuid
        )
        """
    )
    op.execute(
        """
        CREATE POLICY backup_codes_insert ON backup_codes
        FOR INSERT TO app_user
        WITH CHECK (
            organization_id = nullif(current_setting('app.organization_id', true), '')::uuid
        )
        """
    )
    op.execute(
        """
        CREATE POLICY backup_codes_update ON backup_codes
        FOR UPDATE TO app_user
        USING (organization_id = nullif(current_setting('app.organization_id', true), '')::uuid)
        WITH CHECK (
            organization_id = nullif(current_setting('app.organization_id', true), '')::uuid
        )
        """
    )
    op.execute(
        """
        CREATE POLICY backup_codes_delete ON backup_codes
        FOR DELETE TO app_user
        USING (organization_id = nullif(current_setting('app.organization_id', true), '')::uuid)
        """
    )
    op.execute(
        """
        CREATE POLICY sessions_insert ON sessions
        FOR INSERT TO app_user
        WITH CHECK (
            organization_id = nullif(current_setting('app.organization_id', true), '')::uuid
        )
        """
    )
    op.execute(
        """
        CREATE POLICY sessions_update ON sessions
        FOR UPDATE TO app_user
        USING (organization_id = nullif(current_setting('app.organization_id', true), '')::uuid)
        WITH CHECK (
            organization_id = nullif(current_setting('app.organization_id', true), '')::uuid
        )
        """
    )
    op.execute(
        """
        CREATE POLICY audit_log_insert ON audit_log
        FOR INSERT TO app_user
        WITH CHECK (
            organization_id = nullif(current_setting('app.organization_id', true), '')::uuid
        )
        """
    )
    op.execute(
        """
        CREATE POLICY audit_log_bootstrap_insert ON audit_log
        FOR INSERT TO bootstrap_user
        WITH CHECK (
            organization_id = nullif(current_setting('app.organization_id', true), '')::uuid
        )
        """
    )
    op.execute(
        """
        CREATE POLICY organizations_bootstrap_insert ON organizations
        FOR INSERT TO bootstrap_user
        WITH CHECK (id = nullif(current_setting('app.organization_id', true), '')::uuid)
        """
    )

    op.execute("GRANT SELECT ON TABLE users TO app_user")
    op.execute(
        "GRANT UPDATE (password_hash, totp_secret_encrypted, totp_enabled_at, "
        "totp_last_step, last_login_at) ON TABLE users TO app_user"
    )
    op.execute("GRANT INSERT ON TABLE users TO bootstrap_user")
    op.execute("GRANT SELECT, INSERT, DELETE ON TABLE backup_codes TO app_user")
    op.execute("GRANT UPDATE (used_at) ON TABLE backup_codes TO app_user")
    op.execute("GRANT SELECT, INSERT ON TABLE sessions TO app_user")
    op.execute(
        "GRANT UPDATE (last_seen_at, stage, expires_at, revoked_at) ON TABLE sessions TO app_user"
    )
    op.execute("GRANT SELECT, INSERT ON TABLE audit_log TO app_user")
    op.execute("GRANT INSERT ON TABLE audit_log TO bootstrap_user")
    op.execute("GRANT INSERT ON TABLE organizations TO bootstrap_user")


def downgrade() -> None:
    op.execute("DROP POLICY IF EXISTS organizations_bootstrap_insert ON organizations")
    op.execute("DROP TABLE IF EXISTS audit_log")
    op.execute("DROP TABLE IF EXISTS sessions")
    op.execute("DROP TABLE IF EXISTS backup_codes")
    op.execute("DROP TABLE IF EXISTS users")
