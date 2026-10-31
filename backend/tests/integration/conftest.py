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
    users: tuple[UUID, UUID]
    sessions: tuple[UUID, UUID]
    backup_codes: tuple[UUID, UUID]
    audit_logs: tuple[UUID, UUID]


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
    bootstrap_url = os.environ.get("TEST_DATABASE_BOOTSTRAP_URL", "")
    if bootstrap_url:
        try:
            bootstrap_host = urlparse(bootstrap_url).hostname
        except ValueError:
            pytest.fail("L'URL du rôle bootstrap est invalide.")
        if bootstrap_host not in allowed_hosts:
            pytest.fail("Les tests refusent cet hôte de base bootstrap.")
        values["TEST_DATABASE_BOOTSTRAP_URL"] = bootstrap_url
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


@pytest.fixture(scope="session")
def bootstrap_connection(database_urls: dict[str, str]) -> Iterator[Connection[Any]]:
    """Ouvre la connexion bootstrap si son URL de test est fournie."""
    url = database_urls.get("TEST_DATABASE_BOOTSTRAP_URL")
    if not url:
        pytest.skip("TEST_DATABASE_BOOTSTRAP_URL n'est pas définie.")
    connection = psycopg.connect(url)
    try:
        yield connection
    finally:
        if not connection.closed:
            connection.rollback()
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
    users = (uuid4(), uuid4())
    sessions = (uuid4(), uuid4())
    backup_codes = (uuid4(), uuid4())
    audit_logs = (uuid4(), uuid4())
    data = IsolationData(
        organization_a,
        organization_b,
        site_a,
        site_b,
        events_a,
        events_b,
        users,
        sessions,
        backup_codes,
        audit_logs,
    )
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
            """
            INSERT INTO users (id, organization_id, email, password_hash, role)
            VALUES (%s, %s, %s, %s, %s)
            """,
            [
                (
                    users[0],
                    organization_a,
                    f"{users[0]}@a.example.test",
                    "synthetic-hash-a",
                    "owner",
                ),
                (
                    users[1],
                    organization_b,
                    f"{users[1]}@b.example.test",
                    "synthetic-hash-b",
                    "owner",
                ),
            ],
        )
        cursor.executemany(
            """
            INSERT INTO sessions (id, organization_id, user_id, secret_hash, stage, expires_at)
            VALUES (%s, %s, %s, %s, %s, now() + interval '1 hour')
            """,
            [
                (sessions[0], organization_a, users[0], b"session-a", "full"),
                (sessions[1], organization_b, users[1], b"session-b", "full"),
            ],
        )
        cursor.executemany(
            """
            INSERT INTO backup_codes (id, organization_id, user_id, code_hash)
            VALUES (%s, %s, %s, %s)
            """,
            [
                (backup_codes[0], organization_a, users[0], "synthetic-code-a"),
                (backup_codes[1], organization_b, users[1], "synthetic-code-b"),
            ],
        )
        cursor.executemany(
            """
            INSERT INTO audit_log (id, organization_id, user_id, action, outcome)
            VALUES (%s, %s, %s, %s, %s)
            """,
            [
                (audit_logs[0], organization_a, users[0], "fixture", "success"),
                (audit_logs[1], organization_b, users[1], "fixture", "success"),
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
