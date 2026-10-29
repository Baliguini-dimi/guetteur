"""Vérifie la durée de vie transactionnelle du contexte PostgreSQL."""

import pytest
from conftest import IsolationData
from psycopg import Connection

from guetteur.db import set_organization_context


@pytest.mark.integration
def test_organization_context_does_not_leak_between_transactions(
    app_connection: Connection[object], isolation_data: IsolationData
) -> None:
    """Le contexte fixé localement disparaît au commit de la transaction."""
    with app_connection.cursor() as cursor:
        set_organization_context(cursor, isolation_data.organization_a)
        cursor.execute("SELECT count(id) FROM sites")
        row = cursor.fetchone()
    assert row is not None
    assert row[0] == 1

    app_connection.commit()

    with app_connection.cursor() as cursor:
        cursor.execute("SELECT count(id) FROM sites")
        row = cursor.fetchone()
    assert row is not None
    assert row[0] == 0
