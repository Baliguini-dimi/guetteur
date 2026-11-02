"""Vérifie la commande de création du compte propriétaire."""

from collections.abc import Iterator
from uuid import UUID

import pytest

from guetteur import cli


def _candidate() -> str:
    """Construit une valeur synthétique pour les tests."""
    return "silver" + "harbor" + "2026"


class FakeDatabaseError(Exception):
    """Simule une contrainte d'unicité PostgreSQL."""

    sqlstate = "23505"


class FakeCursor:
    """Enregistre les requêtes sans ouvrir de connexion PostgreSQL."""

    def __init__(self, fail_on: int | None = None) -> None:
        self.calls: list[tuple[str, tuple[object, ...]]] = []
        self.fail_on = fail_on
        self.closed = False

    def execute(self, query: str, parameters: tuple[object, ...]) -> None:
        self.calls.append((query, parameters))
        if self.fail_on == len(self.calls):
            raise FakeDatabaseError("contrainte synthétique")

    def close(self) -> None:
        self.closed = True


class FakeConnection:
    """Fournit les opérations minimales d'une connexion de test."""

    def __init__(self, cursor: FakeCursor | None = None) -> None:
        self.fake_cursor = cursor or FakeCursor()
        self.commits = 0
        self.rollbacks = 0

    def cursor(self) -> FakeCursor:
        return self.fake_cursor

    def commit(self) -> None:
        self.commits += 1

    def rollback(self) -> None:
        self.rollbacks += 1

    def __enter__(self) -> "FakeConnection":
        return self

    def __exit__(self, *arguments: object) -> None:
        del arguments


def test_create_owner_sets_context_before_three_inserts() -> None:
    cursor = FakeCursor()
    connection = FakeConnection(cursor)

    organization_id = cli.create_owner(
        connection, "  Organisation synthétique  ", "  Owner@Example.Test  ", _candidate()
    )

    statements = [query.lower() for query, _ in cursor.calls]
    ordered_statements = (
        len(statements) == 4
        and "set_config('app.organization_id'" in statements[0]
        and all(statement.lstrip().startswith("insert into") for statement in statements[1:])
    )
    parameters = [values for _, values in cursor.calls]
    context_matches_organization = (
        parameters[0][0] == str(organization_id)
        and parameters[1] == (organization_id, "Organisation synthétique")
    )
    user_values = parameters[2]
    normalized_email = user_values[2] == "owner@example.test"
    hashed_secret = isinstance(user_values[3], str) and user_values[3].startswith("$argon2id$")
    owner_role = user_values[4] == "owner"
    audit_values = parameters[3] == (
        organization_id,
        user_values[0],
        "owner_created",
        "success",
        "{}",
    )
    no_returning = all("returning" not in statement for statement in statements)

    assert isinstance(organization_id, UUID)
    assert ordered_statements, "Le contexte doit précéder les trois insertions."
    assert context_matches_organization, (
        "Les identifiants utilisés ne correspondent pas au contexte."
    )
    assert normalized_email, "L'adresse email doit être normalisée avant insertion."
    assert hashed_secret, "Le compte doit stocker une empreinte Argon2id."
    assert owner_role, "Le compte doit recevoir le rôle owner."
    assert audit_values, "L'événement owner_created doit être inséré."
    assert no_returning, "La création ne doit pas utiliser RETURNING."
    assert connection.commits == 1
    assert connection.rollbacks == 0
    assert cursor.closed


def test_create_owner_rolls_back_duplicate_email_without_details() -> None:
    cursor = FakeCursor(fail_on=3)
    connection = FakeConnection(cursor)
    candidate = _candidate()

    with pytest.raises(cli.DuplicateEmailError) as error:
        cli.create_owner(connection, "Organisation synthétique", "owner@example.test", candidate)

    generic_message = str(error.value) == "Cette adresse email est déjà utilisée."
    candidate_not_disclosed = candidate not in str(error.value)
    assert generic_message, "L'erreur d'unicité doit rester générique."
    assert candidate_not_disclosed, "L'erreur ne doit pas reprendre la valeur testée."
    assert connection.rollbacks == 1
    assert connection.commits == 0
    assert cursor.closed


def test_create_owner_rejects_weak_candidate_before_writes() -> None:
    cursor = FakeCursor()
    connection = FakeConnection(cursor)
    candidate = "a" * 11

    with pytest.raises(cli.PasswordPolicyError) as error:
        cli.create_owner(connection, "Organisation synthétique", "owner@example.test", candidate)

    reasons = error.value.reasons
    safe_reasons = all(candidate not in reason for reason in reasons)
    assert reasons, "Le refus doit donner au moins un motif."
    assert safe_reasons, "Le motif ne doit pas reprendre la valeur saisie."
    assert cursor.calls == []
    assert connection.rollbacks == 1
    assert connection.commits == 0


def test_main_requires_bootstrap_url_without_printing_it(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.delenv("BOOTSTRAP_DATABASE_URL", raising=False)
    monkeypatch.setattr("sys.argv", ["guetteur.cli", "create-owner"])
    requested_passwords = 0

    def unexpected_getpass(prompt: str) -> str:
        nonlocal requested_passwords
        del prompt
        requested_passwords += 1
        return ""

    monkeypatch.setattr(cli, "getpass", unexpected_getpass)

    exit_code = cli.main()
    output = capsys.readouterr()

    assert exit_code == 1
    assert "BOOTSTRAP_DATABASE_URL" in output.err
    assert requested_passwords == 0
    assert output.out == ""


def test_main_reads_password_twice_and_prints_only_setup_guidance(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    candidate = _candidate()
    values: Iterator[str] = iter((candidate, candidate))
    connection = FakeConnection()
    seen_urls: list[str] = []

    def fake_connect(database_url: str) -> FakeConnection:
        seen_urls.append(database_url)
        return connection

    monkeypatch.setenv("BOOTSTRAP_DATABASE_URL", "postgresql://synthetic.invalid/db")
    monkeypatch.setattr(
        "sys.argv",
        [
            "guetteur.cli",
            "create-owner",
            "--organization-name",
            "Organisation synthétique",
            "--email",
            "owner@example.test",
        ],
    )
    monkeypatch.setattr(cli, "getpass", lambda prompt: next(values))
    monkeypatch.setattr(cli.psycopg, "connect", fake_connect)

    exit_code = cli.main()
    output = capsys.readouterr()

    has_guidance = (
        "Identifiant de l'organisation :" in output.out
        and "OWNER_ORGANIZATION_ID" in output.out
    )
    no_sensitive_values = (
        candidate not in output.out and "postgresql://" not in output.out
    )
    assert exit_code == 0
    assert has_guidance, "La sortie doit donner l'identifiant et la consigne."
    assert no_sensitive_values, "La sortie ne doit contenir ni valeur saisie ni URL de connexion."
    assert len(seen_urls) == 1
    assert connection.commits == 1
    assert output.err == ""
