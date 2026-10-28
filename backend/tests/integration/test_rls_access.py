"""Vérifie l'isolation et les politiques RLS sur PostgreSQL."""

from uuid import UUID, uuid4

import pytest
from conftest import IsolationData
from psycopg import Connection
from psycopg.errors import (
    ForeignKeyViolation,
    InsufficientPrivilege,
    InvalidTextRepresentation,
)

from guetteur.db import set_organization_context


def _count(connection: Connection[object], table: str) -> int:
    """Compte les lignes visibles d'une table connue du test."""
    queries = {
        "organizations": "SELECT count(id) FROM organizations",
        "sites": "SELECT count(id) FROM sites",
        "log_events": "SELECT count(id) FROM log_events",
    }
    with connection.cursor() as cursor:
        cursor.execute(queries[table])
        row = cursor.fetchone()
    assert row is not None
    return int(row[0])


def _set_context(connection: Connection[object], organization_id: UUID) -> None:
    """Fixe le contexte dans un curseur fermé explicitement."""
    with connection.cursor() as cursor:
        set_organization_context(cursor, organization_id)


@pytest.mark.integration
def test_roles_and_row_security_flags(app_connection: Connection[object]) -> None:
    """Les rôles sont limités et les trois tables imposent RLS."""
    with app_connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT rolname, rolsuper, rolbypassrls, rolcreaterole, rolcreatedb
            FROM pg_roles WHERE rolname = ANY(%s)
            """,
            (["app_user", "migration_user"],),
        )
        roles = cursor.fetchall()
        cursor.execute(
            """
            SELECT c.relname, c.relrowsecurity, c.relforcerowsecurity,
                   pg_get_userbyid(c.relowner)
            FROM pg_class AS c JOIN pg_namespace AS n ON n.oid = c.relnamespace
            WHERE n.nspname = %s AND c.relname = ANY(%s)
            """,
            ("public", ["organizations", "sites", "log_events"]),
        )
        tables = cursor.fetchall()
    assert len(roles) == 2
    assert all(not any(row[1:]) for row in roles)
    assert len(tables) == 3
    assert all(row[1] and row[2] and row[3] == "migration_user" for row in tables)
    assert all(row[3] != "app_user" for row in tables)


@pytest.mark.integration
def test_app_user_sees_no_rows_without_context(
    app_connection: Connection[object],
    admin_connection: Connection[object],
    isolation_data: IsolationData,
) -> None:
    """Sans contexte, app_user ne voit aucune ligne organisationnelle."""
    assert isolation_data.organization_a != isolation_data.organization_b
    with admin_connection.cursor() as cursor:
        cursor.execute(
            "SELECT count(id) FROM organizations WHERE id = ANY(%s)",
            ([isolation_data.organization_a, isolation_data.organization_b],),
        )
        row = cursor.fetchone()
    assert row is not None
    assert row[0] == 2
    assert _count(app_connection, "organizations") == 0
    assert _count(app_connection, "sites") == 0
    assert _count(app_connection, "log_events") == 0


@pytest.mark.integration
@pytest.mark.parametrize(
    ("organization_key", "site_key", "events_key"),
    [("organization_a", "site_a", "events_a"), ("organization_b", "site_b", "events_b")],
)
def test_context_exposes_only_one_organization(
    app_connection: Connection[object],
    isolation_data: IsolationData,
    organization_key: str,
    site_key: str,
    events_key: str,
) -> None:
    """Le contexte A ou B ne révèle que ses propres lignes."""
    values = isolation_data._asdict()
    organization_id = values[organization_key]
    site_id = values[site_key]
    event_ids = values[events_key]
    assert isinstance(organization_id, type(isolation_data.organization_a))
    assert isinstance(site_id, type(isolation_data.site_a))
    assert isinstance(event_ids, tuple)
    _set_context(app_connection, organization_id)
    with app_connection.cursor() as cursor:
        cursor.execute("SELECT id FROM organizations")
        assert [row[0] for row in cursor.fetchall()] == [organization_id]
        cursor.execute("SELECT id FROM sites")
        assert [row[0] for row in cursor.fetchall()] == [site_id]
        cursor.execute("SELECT id FROM log_events ORDER BY id")
        assert {row[0] for row in cursor.fetchall()} == set(event_ids)


@pytest.mark.integration
def test_empty_context_exposes_no_rows(
    app_connection: Connection[object], isolation_data: IsolationData
) -> None:
    """Une valeur de contexte vide ne donne accès à aucune ligne."""
    assert isolation_data.site_a
    with app_connection.cursor() as cursor:
        cursor.execute("SELECT set_config(%s, %s, true)", ("app.organization_id", ""))
    assert _count(app_connection, "organizations") == 0
    assert _count(app_connection, "sites") == 0
    assert _count(app_connection, "log_events") == 0


@pytest.mark.integration
def test_invalid_uuid_context_raises_without_exposing_rows(
    app_connection: Connection[object], isolation_data: IsolationData
) -> None:
    """Un contexte qui n'est pas un UUID provoque une erreur PostgreSQL."""
    assert isolation_data.organization_a
    with app_connection.cursor() as cursor:
        cursor.execute("SELECT set_config(%s, %s, true)", ("app.organization_id", "invalid"))
    with pytest.raises(InvalidTextRepresentation) as error:
        _count(app_connection, "organizations")
    assert error.value.sqlstate == "22P02"


@pytest.mark.integration
def test_insert_site_for_another_organization_is_rejected(
    app_connection: Connection[object], isolation_data: IsolationData
) -> None:
    """La RLS refuse l'insertion d'un site de l'organisation B depuis A."""
    _set_context(app_connection, isolation_data.organization_a)
    with pytest.raises(InsufficientPrivilege, match="row-level security") as error:
        with app_connection.cursor() as cursor:
            cursor.execute(
                "INSERT INTO sites (organization_id, name, domain) VALUES (%s, %s, %s)",
                (isolation_data.organization_b, "Site interdit", f"{uuid4()}.example.test"),
            )
    assert error.value.sqlstate == "42501"


@pytest.mark.integration
def test_composite_foreign_key_rejects_site_from_another_organization(
    app_connection: Connection[object], isolation_data: IsolationData
) -> None:
    """La clé étrangère composite refuse un événement A attaché au site B."""
    _set_context(app_connection, isolation_data.organization_a)
    with pytest.raises(ForeignKeyViolation) as error:
        with app_connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO log_events (
                    organization_id, site_id, occurred_at, source_ip,
                    method, path, response_status, source
                ) VALUES (%s, %s, now(), %s, %s, %s, %s, %s)
                """,
                (
                    isolation_data.organization_a,
                    isolation_data.site_b,
                    "192.0.2.11",
                    "GET",
                    "/",
                    200,
                    "sdk",
                ),
            )
    assert error.value.sqlstate == "23503"


@pytest.mark.integration
def test_app_user_can_insert_own_site_and_event(
    app_connection: Connection[object], isolation_data: IsolationData
) -> None:
    """Les écritures valides dans l'organisation courante réussissent."""
    site_id = uuid4()
    _set_context(app_connection, isolation_data.organization_a)
    with app_connection.cursor() as cursor:
        cursor.execute(
            "INSERT INTO sites (id, organization_id, name, domain) VALUES (%s, %s, %s, %s)",
            (site_id, isolation_data.organization_a, "Site valide", f"{site_id}.example.test"),
        )
        cursor.execute(
            """
            INSERT INTO log_events (
                organization_id, site_id, occurred_at, source_ip,
                method, path, response_status, source
            ) VALUES (%s, %s, now(), %s, %s, %s, %s, %s)
            """,
            (isolation_data.organization_a, site_id, "192.0.2.12", "GET", "/", 200, "sdk"),
        )
    assert _count(app_connection, "sites") == 2


@pytest.mark.integration
def test_update_and_delete_of_another_organization_affect_no_rows(
    app_connection: Connection[object], isolation_data: IsolationData
) -> None:
    """Les modifications et suppressions visant l'organisation B n'affectent rien."""
    _set_context(app_connection, isolation_data.organization_a)
    with app_connection.cursor() as cursor:
        cursor.execute(
            "UPDATE sites SET name = %s WHERE id = %s",
            ("Altération", isolation_data.site_b),
        )
        assert cursor.rowcount == 0
        cursor.execute("DELETE FROM sites WHERE id = %s", (isolation_data.site_b,))
        assert cursor.rowcount == 0


@pytest.mark.integration
def test_update_cannot_move_site_to_another_organization(
    app_connection: Connection[object], isolation_data: IsolationData
) -> None:
    """La condition WITH CHECK interdit de déplacer un site vers B."""
    _set_context(app_connection, isolation_data.organization_a)
    with pytest.raises(InsufficientPrivilege, match="row-level security") as error:
        with app_connection.cursor() as cursor:
            cursor.execute(
                "UPDATE sites SET organization_id = %s WHERE id = %s",
                (isolation_data.organization_b, isolation_data.site_a),
            )
    assert error.value.sqlstate == "42501"


@pytest.mark.integration
def test_deleting_site_cascades_its_events(
    app_connection: Connection[object], isolation_data: IsolationData
) -> None:
    """La suppression d'un site supprime ses événements par cascade."""
    _set_context(app_connection, isolation_data.organization_a)
    with app_connection.cursor() as cursor:
        cursor.execute("DELETE FROM sites WHERE id = %s", (isolation_data.site_a,))
        assert cursor.rowcount == 1
        cursor.execute("SELECT count(id) FROM log_events")
        row = cursor.fetchone()
    assert row is not None
    assert row[0] == 0


@pytest.mark.integration
def test_events_cannot_be_updated(
    app_connection: Connection[object], isolation_data: IsolationData
) -> None:
    """app_user n'a pas le droit de modifier le journal d'événements."""
    _set_context(app_connection, isolation_data.organization_a)
    with pytest.raises(InsufficientPrivilege, match="permission denied") as error:
        with app_connection.cursor() as cursor:
            cursor.execute(
                "UPDATE log_events SET path = %s WHERE id = %s",
                ("/changed", isolation_data.events_a[0]),
            )
    assert error.value.sqlstate == "42501"


@pytest.mark.integration
def test_events_cannot_be_deleted(
    app_connection: Connection[object], isolation_data: IsolationData
) -> None:
    """app_user n'a pas le droit de supprimer un événement."""
    _set_context(app_connection, isolation_data.organization_a)
    with pytest.raises(InsufficientPrivilege, match="permission denied") as error:
        with app_connection.cursor() as cursor:
            cursor.execute("DELETE FROM log_events WHERE id = %s", (isolation_data.events_a[0],))
    assert error.value.sqlstate == "42501"


@pytest.mark.integration
def test_events_filtered_by_other_site_are_not_visible(
    app_connection: Connection[object], isolation_data: IsolationData
) -> None:
    """Le contexte B ne révèle aucun événement filtré sur le site A."""
    _set_context(app_connection, isolation_data.organization_b)
    with app_connection.cursor() as cursor:
        cursor.execute("SELECT id FROM log_events WHERE site_id = %s", (isolation_data.site_a,))
        assert cursor.fetchall() == []
