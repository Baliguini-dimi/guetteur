"""Vérifie la création du premier compte sur PostgreSQL."""

from uuid import UUID, uuid4

import pytest
from psycopg import Connection

from guetteur.cli import DuplicateEmailError, PasswordPolicyError, create_owner
from guetteur.db import set_organization_context


def _candidate() -> str:
    """Construit une valeur synthétique conforme à la politique."""
    return "silver" + "harbor" + "2026"


def _remove_organizations(connection: Connection[object], organization_ids: list[UUID]) -> None:
    """Supprime les organisations synthétiques créées par le test."""
    with connection.cursor() as cursor:
        cursor.execute("DELETE FROM organizations WHERE id = ANY(%s)", (organization_ids,))


@pytest.mark.integration
def test_create_owner_inserts_organization_owner_and_audit_row(
    bootstrap_connection: Connection[object], admin_connection: Connection[object]
) -> None:
    """La commande crée les trois lignes attendues sans stocker le secret en clair."""
    organization_id: UUID | None = None
    candidate = _candidate()
    email = f"{uuid4().hex}@example.test"
    try:
        organization_id = create_owner(
            bootstrap_connection, "Organisation synthétique", email, candidate
        )
        with admin_connection.cursor() as cursor:
            cursor.execute(
                "SELECT id, role, password_hash FROM users WHERE organization_id = %s",
                (organization_id,),
            )
            owner_row = cursor.fetchone()
            cursor.execute(
                "SELECT count(*) FROM organizations WHERE id = %s",
                (organization_id,),
            )
            organization_count = cursor.fetchone()[0]
            cursor.execute(
                """
                SELECT count(*) FROM audit_log
                WHERE organization_id = %s AND action = %s AND outcome = %s
                """,
                (organization_id, "owner_created", "success"),
            )
            audit_count = cursor.fetchone()[0]

        valid_owner = owner_row is not None and owner_row[1] == "owner"
        safe_hash = (
            owner_row is not None
            and isinstance(owner_row[2], str)
            and owner_row[2].startswith("$argon2id$")
            and owner_row[2] != candidate
        )
        expected_records = organization_count == 1 and audit_count == 1
        assert valid_owner, "Le compte créé doit avoir le rôle owner."
        assert safe_hash, "L'empreinte Argon2id ne doit pas être égale à la valeur saisie."
        assert expected_records, "L'organisation et l'événement d'audit doivent exister."
    finally:
        if organization_id is not None:
            _remove_organizations(admin_connection, [organization_id])


@pytest.mark.integration
def test_app_user_sees_only_the_created_owner_in_current_organization(
    bootstrap_connection: Connection[object],
    admin_connection: Connection[object],
    app_connection: Connection[object],
) -> None:
    """La RLS rend le propriétaire visible seulement dans son organisation."""
    organization_id: UUID | None = None
    other_organization_id = uuid4()
    email = f"{uuid4().hex}@example.test"
    try:
        organization_id = create_owner(
            bootstrap_connection, "Organisation synthétique", email, _candidate()
        )
        with admin_connection.cursor() as cursor:
            cursor.execute(
                "INSERT INTO organizations (id, name) VALUES (%s, %s)",
                (other_organization_id, "Organisation témoin synthétique"),
            )
            cursor.execute(
                "SELECT id FROM users WHERE organization_id = %s AND email = %s",
                (organization_id, email),
            )
            user_id = cursor.fetchone()[0]

        with app_connection.cursor() as cursor:
            set_organization_context(cursor, organization_id)
            cursor.execute("SELECT id FROM users WHERE id = %s", (user_id,))
            visible_rows = cursor.fetchall()
            set_organization_context(cursor, other_organization_id)
            cursor.execute("SELECT id FROM users WHERE id = %s", (user_id,))
            hidden_rows = cursor.fetchall()

        visible_in_current_organization = visible_rows == [(user_id,)]
        hidden_in_other_organization = hidden_rows == []
        assert visible_in_current_organization, (
            "L'utilisateur doit être visible dans son organisation."
        )
        assert hidden_in_other_organization, (
            "L'utilisateur doit être masqué dans l'autre organisation."
        )
    finally:
        _remove_organizations(admin_connection, [other_organization_id])
        if organization_id is not None:
            _remove_organizations(admin_connection, [organization_id])


@pytest.mark.integration
def test_duplicate_email_rolls_back_the_second_organization(
    bootstrap_connection: Connection[object], admin_connection: Connection[object]
) -> None:
    """Une adresse déjà utilisée annule aussi l'insertion de la seconde organisation."""
    organization_id: UUID | None = None
    test_tag = uuid4().hex
    email = f"{test_tag}@example.test"
    second_name = f"Organisation seconde {test_tag}"
    try:
        organization_id = create_owner(
            bootstrap_connection, "Organisation initiale synthétique", email, _candidate()
        )
        with pytest.raises(DuplicateEmailError) as error:
            create_owner(bootstrap_connection, second_name, email, _candidate())

        safe_error = str(error.value) == "Cette adresse email est déjà utilisée."
        with admin_connection.cursor() as cursor:
            cursor.execute("SELECT count(*) FROM organizations WHERE name = %s", (second_name,))
            orphan_count = cursor.fetchone()[0]
        assert safe_error, "L'erreur de collision doit rester générique."
        assert orphan_count == 0, "La transaction doit annuler l'organisation orpheline."
    finally:
        if organization_id is not None:
            _remove_organizations(admin_connection, [organization_id])


@pytest.mark.integration
def test_weak_candidate_is_refused_before_database_writes(
    bootstrap_connection: Connection[object], admin_connection: Connection[object]
) -> None:
    """Un candidat refusé ne laisse aucune organisation en base."""
    test_tag = uuid4().hex
    organization_name = f"Organisation refusée {test_tag}"
    candidate = "a" * 11

    with pytest.raises(PasswordPolicyError):
        create_owner(
            bootstrap_connection,
            organization_name,
            f"{test_tag}@example.test",
            candidate,
        )

    with admin_connection.cursor() as cursor:
        cursor.execute("SELECT count(*) FROM organizations WHERE name = %s", (organization_name,))
        organization_count = cursor.fetchone()[0]
    assert organization_count == 0, "Le refus de politique doit précéder toute insertion."
