"""Vérifie les droits et l'isolation des tables d'authentification."""

from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import pytest
from conftest import IsolationData
from psycopg import Connection, sql
from psycopg.errors import (
    CheckViolation,
    ForeignKeyViolation,
    InsufficientPrivilege,
    UniqueViolation,
)

from guetteur.db import set_organization_context

TABLE_IDS = [
    ("users", "users"),
    ("backup_codes", "backup_codes"),
    ("sessions", "sessions"),
    ("audit_log", "audit_logs"),
]


def set_context(connection: Connection[object], organization_id: UUID) -> None:
    """Fixe le contexte de l'organisation dans la transaction courante."""
    with connection.cursor() as cursor:
        set_organization_context(cursor, organization_id)


def execute_denied(
    connection: Connection[object], query: str | sql.Composable, parameters: tuple[object, ...]
) -> None:
    """Vérifie un refus dans un point de sauvegarde pour garder la transaction utilisable."""
    with pytest.raises(InsufficientPrivilege) as error:
        execute_in_savepoint(connection, query, parameters)
    assert error.value.sqlstate == "42501"


def execute_in_savepoint(
    connection: Connection[object], query: str | sql.Composable, parameters: tuple[object, ...]
) -> None:
    """Exécute une requête dans un point de sauvegarde PostgreSQL."""
    with connection.transaction():
        with connection.cursor() as cursor:
            cursor.execute(query, parameters)


@pytest.mark.integration
def test_auth_roles_tables_rls_and_ownership(admin_connection: Connection[object]) -> None:
    """Le rôle bootstrap est limité et les nouvelles tables appartiennent aux migrations."""
    with admin_connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT rolcanlogin, rolsuper, rolbypassrls, rolcreaterole, rolcreatedb, rolinherit
            FROM pg_roles WHERE rolname = %s
            """,
            ("bootstrap_user",),
        )
        assert cursor.fetchone() == (True, False, False, False, False, False)
        cursor.execute(
            """
            SELECT count(*) FROM pg_class AS c
            JOIN pg_namespace AS n ON n.oid = c.relnamespace
            WHERE n.nspname = %s AND c.relkind IN ('r', 'p')
              AND pg_get_userbyid(c.relowner) = %s
            """,
            ("public", "bootstrap_user"),
        )
        assert cursor.fetchone() == (0,)
        cursor.execute(
            """
            SELECT c.relname, c.relrowsecurity, c.relforcerowsecurity,
                   pg_get_userbyid(c.relowner)
            FROM pg_class AS c JOIN pg_namespace AS n ON n.oid = c.relnamespace
            WHERE n.nspname = %s AND c.relname = ANY(%s)
            """,
            ("public", ["users", "backup_codes", "sessions", "audit_log"]),
        )
        rows = cursor.fetchall()
    assert len(rows) == 4
    assert all(row[1] and row[2] and row[3] == "migration_user" for row in rows)
    with admin_connection.cursor() as cursor:
        for table in (
            "organizations",
            "sites",
            "log_events",
            "users",
            "backup_codes",
            "sessions",
            "audit_log",
            "alembic_version",
        ):
            for privilege in ("SELECT", "UPDATE", "DELETE"):
                cursor.execute(
                    "SELECT has_table_privilege(%s, %s, %s)",
                    ("bootstrap_user", table, privilege),
                )
                assert cursor.fetchone() == (False,)


@pytest.mark.integration
@pytest.mark.parametrize(("table", "ids_key"), TABLE_IDS)
def test_auth_tables_hide_rows_without_context(
    app_connection: Connection[object], isolation_data: IsolationData, table: str, ids_key: str
) -> None:
    """Sans contexte, aucune ligne d'authentification n'est visible."""
    del ids_key
    with app_connection.cursor() as cursor:
        cursor.execute(sql.SQL("SELECT id FROM {}").format(sql.Identifier(table)))
        assert cursor.fetchall() == []


@pytest.mark.integration
@pytest.mark.parametrize(("table", "ids_key"), TABLE_IDS)
@pytest.mark.parametrize(("org_key", "row_index"), [("organization_a", 0), ("organization_b", 1)])
def test_auth_tables_show_only_current_organization(
    app_connection: Connection[object],
    isolation_data: IsolationData,
    table: str,
    ids_key: str,
    org_key: str,
    row_index: int,
) -> None:
    """Les quatre tables ne montrent que la ligne de l'organisation courante."""
    set_context(app_connection, getattr(isolation_data, org_key))
    with app_connection.cursor() as cursor:
        cursor.execute(sql.SQL("SELECT id FROM {}").format(sql.Identifier(table)))
        ids = {row[0] for row in cursor.fetchall()}
    expected = getattr(isolation_data, ids_key)[row_index]
    other = getattr(isolation_data, ids_key)[1 - row_index]
    assert ids == {expected}
    assert other not in ids


@pytest.mark.integration
@pytest.mark.parametrize(
    ("table", "query", "parameters_factory"),
    [
        (
            "backup_codes",
            "INSERT INTO backup_codes (id, organization_id, "
            "user_id, code_hash) VALUES (%s, %s, %s, %s)",
            lambda data: (uuid4(), data.organization_a, data.users[0], "positive-code"),
        ),
        (
            "sessions",
            "INSERT INTO sessions (id, organization_id, user_id, "
            "secret_hash, stage, expires_at) VALUES (%s, %s, %s, %s, %s, %s)",
            lambda data: (
                uuid4(),
                data.organization_a,
                data.users[0],
                uuid4().bytes,
                "full",
                datetime.now(UTC) + timedelta(hours=1),
            ),
        ),
        (
            "audit_log",
            "INSERT INTO audit_log (id, organization_id, user_id, "
            "action, outcome) VALUES (%s, %s, %s, %s, %s)",
            lambda data: (uuid4(), data.organization_a, data.users[0], "positive", "success"),
        ),
    ],
)
def test_app_user_can_insert_auth_data_in_own_organization(
    app_connection: Connection[object],
    isolation_data: IsolationData,
    table: str,
    query: str,
    parameters_factory: Callable[[IsolationData], tuple[object, ...]],
) -> None:
    """Les insertions valides sont permises dans l'organisation courante."""
    set_context(app_connection, isolation_data.organization_a)
    parameters = parameters_factory(isolation_data)
    with app_connection.cursor() as cursor:
        cursor.execute(query, parameters)
        assert cursor.rowcount == 1


@pytest.mark.integration
@pytest.mark.parametrize(
    ("query", "parameters_factory"),
    [
        (
            "INSERT INTO backup_codes (id, organization_id, "
            "user_id, code_hash) VALUES (%s, %s, %s, %s)",
            lambda data: (uuid4(), data.organization_b, data.users[1], "cross-code"),
        ),
        (
            "INSERT INTO sessions (id, organization_id, user_id, "
            "secret_hash, stage, expires_at) VALUES (%s, %s, %s, %s, %s, %s)",
            lambda data: (
                uuid4(),
                data.organization_b,
                data.users[1],
                uuid4().bytes,
                "full",
                datetime.now(UTC) + timedelta(hours=1),
            ),
        ),
        (
            "INSERT INTO audit_log (id, organization_id, user_id, "
            "action, outcome) VALUES (%s, %s, %s, %s, %s)",
            lambda data: (uuid4(), data.organization_b, data.users[1], "cross", "failure"),
        ),
    ],
)
def test_app_user_cannot_insert_auth_data_for_other_organization(
    app_connection: Connection[object],
    isolation_data: IsolationData,
    query: str,
    parameters_factory: Callable[[IsolationData], tuple[object, ...]],
) -> None:
    """La RLS refuse chaque insertion croisée."""
    set_context(app_connection, isolation_data.organization_a)
    parameters = parameters_factory(isolation_data)
    execute_denied(app_connection, query, parameters)


@pytest.mark.integration
def test_session_composite_foreign_key_rejects_another_organization_user(
    app_connection: Connection[object], isolation_data: IsolationData
) -> None:
    """Une session A ne peut pas être rattachée à l'utilisateur B."""
    set_context(app_connection, isolation_data.organization_a)
    with pytest.raises(ForeignKeyViolation) as error:
        execute_in_savepoint(
            app_connection,
            "INSERT INTO sessions (organization_id, user_id, secret_hash, stage, expires_at) "
            "VALUES (%s, %s, %s, %s, %s)",
            (
                isolation_data.organization_a,
                isolation_data.users[1],
                uuid4().bytes,
                "full",
                datetime.now(UTC) + timedelta(hours=1),
            ),
        )
    assert error.value.sqlstate == "23503"


@pytest.mark.integration
@pytest.mark.parametrize(
    ("query", "parameters"),
    [
        (
            "INSERT INTO users (organization_id, email, "
            "password_hash, role) VALUES (%s, %s, %s, %s)",
            (uuid4(), "new@example.test", "synthetic-hash", "owner"),
        ),
        ("DELETE FROM users WHERE id = %s", (uuid4(),)),
    ],
)
def test_app_user_cannot_insert_or_delete_users(
    app_connection: Connection[object],
    isolation_data: IsolationData,
    query: str,
    parameters: tuple[object, ...],
) -> None:
    """app_user ne peut ni créer ni supprimer un compte."""
    set_context(app_connection, isolation_data.organization_a)
    execute_denied(app_connection, query, parameters)


@pytest.mark.integration
def test_app_user_can_update_own_password_and_totp_step(
    app_connection: Connection[object], isolation_data: IsolationData
) -> None:
    """app_user peut modifier le hash et le pas TOTP de son compte."""
    set_context(app_connection, isolation_data.organization_a)
    with app_connection.cursor() as cursor:
        cursor.execute(
            "UPDATE users SET password_hash = %s WHERE id = %s",
            ("updated-hash", isolation_data.users[0]),
        )
        assert cursor.rowcount == 1
        cursor.execute(
            "UPDATE users SET totp_last_step = %s WHERE id = %s", (123456, isolation_data.users[0])
        )
        assert cursor.rowcount == 1


@pytest.mark.integration
def test_app_user_cannot_update_another_users_password(
    app_connection: Connection[object], isolation_data: IsolationData
) -> None:
    """La RLS masque le compte B lors d'une mise à jour depuis A."""
    set_context(app_connection, isolation_data.organization_a)
    with app_connection.cursor() as cursor:
        cursor.execute(
            "UPDATE users SET password_hash = %s WHERE id = %s",
            ("ignored", isolation_data.users[1]),
        )
        assert cursor.rowcount == 0


@pytest.mark.integration
@pytest.mark.parametrize(
    ("column", "value"),
    [("role", "admin"), ("organization_id", uuid4()), ("email", "changed@example.test")],
)
def test_app_user_cannot_update_restricted_user_columns(
    app_connection: Connection[object], isolation_data: IsolationData, column: str, value: object
) -> None:
    """Les colonnes d'identité et d'autorisation restent immuables pour app_user."""
    set_context(app_connection, isolation_data.organization_a)
    execute_denied(
        app_connection,
        sql.SQL("UPDATE users SET {} = %s WHERE id = %s").format(sql.Identifier(column)),
        (value, isolation_data.users[0]),
    )


@pytest.mark.integration
@pytest.mark.parametrize(
    ("column", "value"),
    [
        ("last_seen_at", datetime.now(UTC)),
        ("stage", "provisional"),
        ("expires_at", datetime.now(UTC) + timedelta(hours=2)),
        ("revoked_at", datetime.now(UTC)),
    ],
)
def test_app_user_can_update_allowed_session_columns(
    app_connection: Connection[object], isolation_data: IsolationData, column: str, value: object
) -> None:
    """Les colonnes de cycle de vie autorisées d'une session sont modifiables."""
    set_context(app_connection, isolation_data.organization_a)
    with app_connection.cursor() as cursor:
        cursor.execute(
            sql.SQL("UPDATE sessions SET {} = %s WHERE id = %s").format(sql.Identifier(column)),
            (value, isolation_data.sessions[0]),
        )
        assert cursor.rowcount == 1


@pytest.mark.integration
@pytest.mark.parametrize(
    ("column", "value"),
    [("organization_id", uuid4()), ("user_id", uuid4()), ("secret_hash", uuid4().bytes)],
)
def test_app_user_cannot_update_identity_session_columns(
    app_connection: Connection[object], isolation_data: IsolationData, column: str, value: object
) -> None:
    """Les identifiants et secrets de session ne sont pas modifiables."""
    set_context(app_connection, isolation_data.organization_a)
    execute_denied(
        app_connection,
        sql.SQL("UPDATE sessions SET {} = %s WHERE id = %s").format(sql.Identifier(column)),
        (value, isolation_data.sessions[0]),
    )


@pytest.mark.integration
def test_app_user_cannot_delete_sessions(
    app_connection: Connection[object], isolation_data: IsolationData
) -> None:
    """app_user ne peut pas supprimer les sessions."""
    set_context(app_connection, isolation_data.organization_a)
    execute_denied(
        app_connection, "DELETE FROM sessions WHERE id = %s", (isolation_data.sessions[0],)
    )


@pytest.mark.integration
def test_audit_log_is_append_only_for_app_user(
    app_connection: Connection[object], isolation_data: IsolationData
) -> None:
    """app_user peut ajouter une ligne, mais ne peut ni la modifier ni la supprimer."""
    set_context(app_connection, isolation_data.organization_a)
    with app_connection.cursor() as cursor:
        cursor.execute(
            "INSERT INTO audit_log (organization_id, user_id, "
            "action, outcome) VALUES (%s, %s, %s, %s)",
            (isolation_data.organization_a, isolation_data.users[0], "test", "success"),
        )
    execute_denied(
        app_connection,
        "UPDATE audit_log SET action = %s WHERE id = %s",
        ("mutated", isolation_data.audit_logs[0]),
    )
    execute_denied(
        app_connection, "DELETE FROM audit_log WHERE id = %s", (isolation_data.audit_logs[0],)
    )


@pytest.mark.integration
def test_backup_code_permissions(
    app_connection: Connection[object], isolation_data: IsolationData
) -> None:
    """app_user peut lire, créer, consommer et supprimer ses codes de secours."""
    set_context(app_connection, isolation_data.organization_a)
    with app_connection.cursor() as cursor:
        cursor.execute(
            "SELECT id FROM backup_codes WHERE id = %s", (isolation_data.backup_codes[0],)
        )
        assert cursor.fetchone() == (isolation_data.backup_codes[0],)
        cursor.execute(
            "INSERT INTO backup_codes (organization_id, user_id, code_hash) VALUES (%s, %s, %s)",
            (isolation_data.organization_a, isolation_data.users[0], "new-code"),
        )
        cursor.execute(
            "UPDATE backup_codes SET used_at = now() WHERE id = %s",
            (isolation_data.backup_codes[0],),
        )
        assert cursor.rowcount == 1
    execute_denied(
        app_connection,
        "UPDATE backup_codes SET code_hash = %s WHERE id = %s",
        ("changed", isolation_data.backup_codes[0]),
    )
    with app_connection.cursor() as cursor:
        cursor.execute("DELETE FROM backup_codes WHERE id = %s", (isolation_data.backup_codes[0],))
        assert cursor.rowcount == 1


@pytest.mark.integration
def test_bootstrap_user_creates_first_organization_owner_and_audit(
    bootstrap_connection: Connection[object], admin_connection: Connection[object]
) -> None:
    """Le rôle bootstrap crée les trois objets avec des identifiants préparés côté client."""
    organization_id, user_id, audit_id = uuid4(), uuid4(), uuid4()
    try:
        set_context(bootstrap_connection, organization_id)
        with bootstrap_connection.cursor() as cursor:
            cursor.execute(
                "INSERT INTO organizations (id, name) VALUES (%s, %s)",
                (organization_id, "Organisation bootstrap synthétique"),
            )
            cursor.execute(
                "INSERT INTO users (id, organization_id, email, "
                "password_hash, role) VALUES (%s, %s, %s, %s, %s)",
                (
                    user_id,
                    organization_id,
                    f"{user_id}@bootstrap.example.test",
                    "synthetic-hash",
                    "owner",
                ),
            )
            cursor.execute(
                "INSERT INTO audit_log (id, organization_id, user_id, "
                "action, outcome) VALUES (%s, %s, %s, %s, %s)",
                (audit_id, organization_id, user_id, "bootstrap", "success"),
            )
        bootstrap_connection.commit()
    finally:
        bootstrap_connection.rollback()
        with admin_connection.cursor() as cursor:
            cursor.execute("DELETE FROM organizations WHERE id = %s", (organization_id,))


@pytest.mark.integration
def test_bootstrap_user_cannot_create_non_owner(
    bootstrap_connection: Connection[object], admin_connection: Connection[object]
) -> None:
    """La politique réservée au bootstrap refuse la création d'un rôle autre que owner."""
    organization_id = uuid4()
    with admin_connection.cursor() as cursor:
        cursor.execute(
            "INSERT INTO organizations (id, name) VALUES (%s, %s)",
            (organization_id, "Organisation bootstrap synthétique"),
        )
    try:
        set_context(bootstrap_connection, organization_id)
        execute_denied(
            bootstrap_connection,
            "INSERT INTO users (id, organization_id, email, password_hash, role) "
            "VALUES (%s, %s, %s, %s, %s)",
            (
                uuid4(),
                organization_id,
                f"{uuid4()}@denied.example.test",
                "synthetic-hash",
                "admin",
            ),
        )
    finally:
        bootstrap_connection.rollback()
        with admin_connection.cursor() as cursor:
            cursor.execute("DELETE FROM organizations WHERE id = %s", (organization_id,))


@pytest.mark.integration
@pytest.mark.parametrize(
    "table",
    [
        "organizations",
        "sites",
        "log_events",
        "users",
        "backup_codes",
        "sessions",
        "audit_log",
        "alembic_version",
    ],
)
def test_bootstrap_user_cannot_select_tables(
    bootstrap_connection: Connection[object], table: str
) -> None:
    """bootstrap_user ne possède aucun droit de lecture."""
    query = sql.SQL("SELECT * FROM {}").format(sql.Identifier(table))
    with pytest.raises(InsufficientPrivilege) as error:
        with bootstrap_connection.cursor() as cursor:
            cursor.execute(query)
    assert error.value.sqlstate == "42501"
    bootstrap_connection.rollback()


@pytest.mark.integration
@pytest.mark.parametrize(
    ("query", "parameters"),
    [
        ("UPDATE organizations SET name = %s", ("forbidden",)),
        ("DELETE FROM organizations", ()),
        ("UPDATE users SET role = %s", ("admin",)),
        ("DELETE FROM users", ()),
        ("UPDATE audit_log SET action = %s", ("forbidden",)),
        ("DELETE FROM audit_log", ()),
        (
            "INSERT INTO sessions (organization_id, user_id, "
            "secret_hash, stage, expires_at) VALUES (%s, %s, %s, %s, %s)",
            (uuid4(), uuid4(), uuid4().bytes, "full", datetime.now(UTC) + timedelta(hours=1)),
        ),
        (
            "INSERT INTO backup_codes (organization_id, user_id, code_hash) VALUES (%s, %s, %s)",
            (uuid4(), uuid4(), "denied"),
        ),
    ],
)
def test_bootstrap_user_cannot_mutate_or_create_session_data(
    bootstrap_connection: Connection[object], query: str, parameters: tuple[object, ...]
) -> None:
    """bootstrap_user ne peut modifier ni supprimer et ne crée pas de sessions ou codes."""
    with pytest.raises(InsufficientPrivilege) as error:
        with bootstrap_connection.cursor() as cursor:
            cursor.execute(query, parameters)
    assert error.value.sqlstate == "42501"
    bootstrap_connection.rollback()


@pytest.mark.integration
def test_constraints_reject_uppercase_email(
    admin_connection: Connection[object], isolation_data: IsolationData
) -> None:
    """La contrainte impose des adresses en minuscules."""
    with pytest.raises(CheckViolation) as error:
        with admin_connection.cursor() as cursor:
            cursor.execute(
                "INSERT INTO users (organization_id, email, "
                "password_hash, role) VALUES (%s, %s, %s, %s)",
                (
                    isolation_data.organization_a,
                    f"UPPER-{uuid4()}@example.test",
                    "synthetic",
                    "owner",
                ),
            )
    assert error.value.sqlstate == "23514"


@pytest.mark.integration
def test_constraints_reject_duplicate_email(
    admin_connection: Connection[object], isolation_data: IsolationData
) -> None:
    """L'adresse email est unique globalement."""
    with pytest.raises(UniqueViolation) as error:
        with admin_connection.cursor() as cursor:
            cursor.execute(
                "INSERT INTO users (organization_id, email, "
                "password_hash, role) VALUES (%s, %s, %s, %s)",
                (
                    isolation_data.organization_b,
                    f"{isolation_data.users[0]}@a.example.test",
                    "synthetic",
                    "owner",
                ),
            )
    assert error.value.sqlstate == "23505"


@pytest.mark.integration
def test_constraints_reject_invalid_user_role(
    admin_connection: Connection[object], isolation_data: IsolationData
) -> None:
    """La contrainte refuse les rôles qui ne figurent pas dans la liste."""
    with pytest.raises(CheckViolation) as error:
        with admin_connection.cursor() as cursor:
            cursor.execute(
                "INSERT INTO users (organization_id, email, "
                "password_hash, role) VALUES (%s, %s, %s, %s)",
                (
                    isolation_data.organization_a,
                    f"{uuid4()}@example.test",
                    "synthetic",
                    "superuser",
                ),
            )
    assert error.value.sqlstate == "23514"


@pytest.mark.integration
def test_constraints_reject_invalid_session_stage(
    admin_connection: Connection[object], isolation_data: IsolationData
) -> None:
    """La contrainte refuse une étape de session inconnue."""
    with pytest.raises(CheckViolation) as error:
        with admin_connection.cursor() as cursor:
            cursor.execute(
                "INSERT INTO sessions (organization_id, user_id, "
                "secret_hash, stage, expires_at) VALUES (%s, %s, %s, %s, %s)",
                (
                    isolation_data.organization_a,
                    isolation_data.users[0],
                    uuid4().bytes,
                    "invalid",
                    datetime.now(UTC) + timedelta(hours=1),
                ),
            )
    assert error.value.sqlstate == "23514"
