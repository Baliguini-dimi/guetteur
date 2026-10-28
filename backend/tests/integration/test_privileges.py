"""Vérifie les privilèges SQL accordés à app_user."""

from uuid import uuid4

import pytest
from conftest import IsolationData
from psycopg import Connection
from psycopg.errors import InsufficientPrivilege

from guetteur.db import set_organization_context


@pytest.mark.integration
@pytest.mark.parametrize(
    ("query", "parameters"),
    [
        (
            "INSERT INTO organizations (id, name) VALUES (%s, %s)",
            (uuid4(), "Organisation interdite"),
        ),
        ("UPDATE organizations SET name = %s WHERE id = %s", ("Altération", uuid4())),
        ("DELETE FROM organizations WHERE id = %s", (uuid4(),)),
    ],
)
def test_app_user_cannot_write_organizations(
    app_connection: Connection[object],
    isolation_data: IsolationData,
    query: str,
    parameters: tuple[object, ...],
) -> None:
    """app_user ne peut créer, modifier ou supprimer une organisation."""
    with app_connection.cursor() as context_cursor:
        set_organization_context(context_cursor, isolation_data.organization_a)
    with pytest.raises(InsufficientPrivilege, match="permission denied") as error:
        with app_connection.cursor() as cursor:
            cursor.execute(query, parameters)
    assert error.value.sqlstate == "42501"


@pytest.mark.integration
@pytest.mark.parametrize(
    ("query", "parameters"),
    [
        ("SELECT version_num FROM alembic_version", None),
        ("UPDATE alembic_version SET version_num = %s", ("invalid",)),
    ],
)
def test_app_user_cannot_access_alembic_version(
    app_connection: Connection[object],
    query: str,
    parameters: tuple[str, ...] | None,
) -> None:
    """app_user n'a aucun accès en lecture ou écriture à alembic_version."""
    with pytest.raises(InsufficientPrivilege, match="permission denied") as error:
        with app_connection.cursor() as cursor:
            cursor.execute(query, parameters)
    assert error.value.sqlstate == "42501"


@pytest.mark.integration
def test_app_user_cannot_create_public_table(app_connection: Connection[object]) -> None:
    """app_user ne peut pas créer de table dans le schéma public."""
    with pytest.raises(InsufficientPrivilege, match="permission denied") as error:
        with app_connection.cursor() as cursor:
            cursor.execute("CREATE TABLE public.forbidden_test_table (id integer)")
    assert error.value.sqlstate == "42501"


@pytest.mark.integration
def test_app_user_cannot_disable_row_security(app_connection: Connection[object]) -> None:
    """app_user ne peut pas désactiver la RLS de sites."""
    with pytest.raises(InsufficientPrivilege) as error:
        with app_connection.cursor() as cursor:
            cursor.execute("ALTER TABLE sites DISABLE ROW LEVEL SECURITY")
    assert error.value.sqlstate == "42501"
