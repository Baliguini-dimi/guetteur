"""Prépare une base PostgreSQL locale pour les tests d'isolation."""

import os
from collections.abc import Iterator
from datetime import UTC, datetime
from typing import Any, NamedTuple
from urllib.parse import urlparse
from uuid import UUID, uuid4

import psycopg
import pytest
from psycopg import Connection


class IsolationData(NamedTuple):
    """Identifiants synthétiques utilisés par un test d'isolation."""

    organization_a: UUID
    organization_b: UUID
    site_a: UUID
    site_b: UUID
    events_a: tuple[UUID, UUID]
    events_b: tuple[UUID, UUID]


def _database_urls() -> dict[str, str]:
    """Lit et valide les trois URL sans jamais les inclure dans un message."""
    names = (
        "TEST_DATABASE_ADMIN_URL",
        "TEST_DATABASE_APP_URL",
        "TEST_DATABASE_MIGRATION_URL",
    )
    values = {name: os.environ.get(name, "") for name in names}
    if any(not value for value in values.values()):
        pytest.skip("Les variables TEST_DATABASE_* ne sont pas toutes définies.")
    allowed_hosts = {"127.0.0.1", "localhost", "db"}
    for value in values.values():
        try:
            host = urlparse(value).hostname
        except ValueError:
            pytest.fail("Une URL de base de test est invalide.")
        if host not in allowed_hosts:
            pytest.fail("Les tests d'intégration refusent cet hôte de base de données.")
    return values


@pytest.fixture(scope="session")
def database_urls() -> dict[str, str]:
    """Vérifie les variables et l'hôte avant toute connexion PostgreSQL."""
    return _database_urls()


@pytest.fixture(scope="session")
def admin_connection(database_urls: dict[str, str]) -> Iterator[Connection[Any]]:
    """Ouvre une connexion administrateur en mode autocommit."""
    connection = psycopg.connect(database_urls["TEST_DATABASE_ADMIN_URL"], autocommit=True)
    try:
        yield connection
    finally:
        connection.close()


@pytest.fixture
def app_connection(
    database_urls: dict[str, str], isolation_data: IsolationData
) -> Iterator[Connection[Any]]:
    """Ouvre une connexion applicative neuve et annule sa transaction."""
    del isolation_data
    connection = psycopg.connect(database_urls["TEST_DATABASE_APP_URL"])
    try:
        yield connection
    finally:
        if not connection.closed:
            connection.rollback()
            connection.close()


@pytest.fixture
def isolation_data(admin_connection: Connection[Any]) -> Iterator[IsolationData]:
    """Crée puis supprime deux organisations et leurs données synthétiques."""
    organization_a, organization_b = uuid4(), uuid4()
    site_a, site_b = uuid4(), uuid4()
    events_a = (uuid4(), uuid4())
    events_b = (uuid4(), uuid4())
    data = IsolationData(organization_a, organization_b, site_a, site_b, events_a, events_b)
    occurred_at = datetime.now(UTC)
    with admin_connection.cursor() as cursor:
        cursor.executemany(
            "INSERT INTO organizations (id, name) VALUES (%s, %s)",
            [
                (organization_a, "Organisation A synthétique"),
                (organization_b, "Organisation B synthétique"),
            ],
        )
        cursor.executemany(
            "INSERT INTO sites (id, organization_id, name, domain) VALUES (%s, %s, %s, %s)",
            [
                (site_a, organization_a, "Site A", f"{site_a}.example.test"),
                (site_b, organization_b, "Site B", f"{site_b}.example.test"),
            ],
        )
        cursor.executemany(
            """
            INSERT INTO log_events (
                id, organization_id, site_id, occurred_at, source_ip,
                method, path, response_status, source
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            [
                (
                    event_id,
                    organization_id,
                    site_id,
                    occurred_at,
                    "192.0.2.10",
                    "GET",
                    "/",
                    200,
                    "sdk",
                )
                for organization_id, site_id, event_ids in (
                    (organization_a, site_a, events_a),
                    (organization_b, site_b, events_b),
                )
                for event_id in event_ids
            ],
        )
    try:
        yield data
    finally:
        with admin_connection.cursor() as cursor:
            cursor.execute(
                "DELETE FROM organizations WHERE id = ANY(%s)",
                ([organization_a, organization_b],),
            )
