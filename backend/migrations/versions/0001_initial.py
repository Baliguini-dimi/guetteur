"""Crée les tables V1a et impose leur isolation PostgreSQL par organisation.

La purge de rétention des événements bruts exigera un rôle dédié, créé dans une
tâche ultérieure.
"""

from alembic import op

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE organizations (
            id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            name varchar(120) NOT NULL,
            created_at timestamptz NOT NULL DEFAULT now()
        )
        """
    )
    op.execute("ALTER TABLE organizations ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE organizations FORCE ROW LEVEL SECURITY")
    op.execute(
        """
        CREATE POLICY organizations_select ON organizations
        FOR SELECT
        USING (id = nullif(current_setting('app.organization_id', true), '')::uuid)
        """
    )
    op.execute("GRANT SELECT ON TABLE organizations TO app_user")

    op.execute(
        """
        CREATE TABLE sites (
            id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            organization_id uuid NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
            name varchar(120) NOT NULL,
            domain varchar(253) NOT NULL,
            created_at timestamptz NOT NULL DEFAULT now(),
            CONSTRAINT sites_id_organization_id_unique UNIQUE (id, organization_id),
            CONSTRAINT sites_organization_domain_unique UNIQUE (organization_id, domain)
        )
        """
    )
    op.execute(
        """
        CREATE TABLE log_events (
            id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            organization_id uuid NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
            site_id uuid NOT NULL,
            occurred_at timestamptz NOT NULL,
            source_ip inet NOT NULL,
            method varchar(10) NOT NULL,
            path varchar(2048) NOT NULL,
            masked_parameters jsonb NOT NULL DEFAULT '{}'::jsonb,
            response_status smallint NOT NULL CHECK (response_status BETWEEN 100 AND 599),
            user_agent varchar(512),
            source varchar(16) NOT NULL CHECK (source IN ('sdk', 'collector')),
            created_at timestamptz NOT NULL DEFAULT now(),
            CONSTRAINT log_events_site_organization_fk
                FOREIGN KEY (site_id, organization_id)
                REFERENCES sites (id, organization_id) ON DELETE CASCADE
        )
        """
    )
    op.execute(
        "CREATE INDEX log_events_org_time_idx ON log_events (organization_id, occurred_at DESC)"
    )
    op.execute("CREATE INDEX log_events_site_time_idx ON log_events (site_id, occurred_at DESC)")

    for table in ("sites", "log_events"):
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
        op.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY")
        op.execute(
            f"""
            CREATE POLICY {table}_select ON {table}
            FOR SELECT
            USING (organization_id = nullif(current_setting('app.organization_id', true), '')::uuid)
            """
        )
        op.execute(
            f"""
            CREATE POLICY {table}_insert ON {table}
            FOR INSERT
            WITH CHECK (
                organization_id = nullif(current_setting('app.organization_id', true), '')::uuid
            )
            """
        )

    op.execute(
        """
        CREATE POLICY sites_delete ON sites
        FOR DELETE
        USING (organization_id = nullif(current_setting('app.organization_id', true), '')::uuid)
        """
    )
    op.execute(
        """
        CREATE POLICY sites_update ON sites
        FOR UPDATE
        USING (organization_id = nullif(current_setting('app.organization_id', true), '')::uuid)
        WITH CHECK (
            organization_id = nullif(current_setting('app.organization_id', true), '')::uuid
        )
        """
    )
    op.execute("GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE sites TO app_user")
    op.execute("GRANT SELECT, INSERT ON TABLE log_events TO app_user")


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS log_events")
    op.execute("DROP TABLE IF EXISTS sites")
    op.execute("DROP TABLE IF EXISTS organizations")
