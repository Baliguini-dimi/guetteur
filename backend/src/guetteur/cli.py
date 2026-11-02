"""Commandes d'administration exécutées depuis le backend Guetteur."""

import argparse
import os
import sys
from getpass import getpass
from uuid import UUID, uuid4

import psycopg
from psycopg import Connection

from guetteur.db import set_organization_context
from guetteur.security.passwords import hash_password, validate_password_policy


class OwnerCreationError(Exception):
    """Erreur de création présentable sans détail interne."""


class PasswordPolicyError(OwnerCreationError):
    """Refus du mot de passe avec des motifs sans donnée sensible."""

    def __init__(self, reasons: list[str]) -> None:
        super().__init__(" ".join(reasons))
        self.reasons = tuple(reasons)


class DuplicateEmailError(OwnerCreationError):
    """Adresse déjà utilisée par un compte."""

    def __init__(self) -> None:
        super().__init__("Cette adresse email est déjà utilisée.")


def _normalize_email(email: str) -> str:
    """Normalise et valide les contraintes simples de l'adresse email."""
    normalized = email.strip().lower()
    if (
        len(normalized) > 254
        or normalized.count("@") != 1
        or any(character.isspace() for character in normalized)
    ):
        raise OwnerCreationError("L'adresse email est invalide.")
    local_part, domain = normalized.split("@")
    if not local_part or not domain:
        raise OwnerCreationError("L'adresse email est invalide.")
    return normalized


def _rollback(connection: Connection[object]) -> None:
    """Annule la transaction sans laisser remonter une erreur interne."""
    try:
        connection.rollback()
    except Exception:
        return


def create_owner(
    connection: Connection[object], organization_name: str, email: str, password: str
) -> UUID:
    """Crée l'organisation et son premier compte dans une transaction."""
    try:
        normalized_name = organization_name.strip()
        if not 1 <= len(normalized_name) <= 120:
            raise OwnerCreationError(
                "Le nom de l'organisation doit contenir de 1 à 120 caractères."
            )
        normalized_email = _normalize_email(email)
        reasons = validate_password_policy(password, normalized_email)
        if reasons:
            raise PasswordPolicyError(reasons)

        password_hash = hash_password(password)
        organization_id = uuid4()
        user_id = uuid4()
        cursor = connection.cursor()
        try:
            set_organization_context(cursor, organization_id)
            cursor.execute(
                "INSERT INTO organizations (id, name) VALUES (%s, %s)",
                (organization_id, normalized_name),
            )
            cursor.execute(
                """
                INSERT INTO users (id, organization_id, email, password_hash, role)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (user_id, organization_id, normalized_email, password_hash, "owner"),
            )
            cursor.execute(
                """
                INSERT INTO audit_log (
                    organization_id, user_id, action, outcome, details
                ) VALUES (%s, %s, %s, %s, %s::jsonb)
                """,
                (organization_id, user_id, "owner_created", "success", "{}"),
            )
        finally:
            cursor.close()
        connection.commit()
        return organization_id
    except PasswordPolicyError:
        _rollback(connection)
        raise
    except OwnerCreationError:
        _rollback(connection)
        raise
    except Exception as error:
        _rollback(connection)
        if getattr(error, "sqlstate", None) == "23505":
            raise DuplicateEmailError() from None
        raise OwnerCreationError("La création du compte propriétaire a échoué.") from None


def _read_value(value: str | None, prompt: str) -> str:
    """Retourne une option fournie ou demande sa valeur au terminal."""
    if value is not None:
        return value
    return input(prompt)


def main() -> int:
    """Exécute la sous-commande de création du premier compte."""
    parser = argparse.ArgumentParser(description="Administration du backend Guetteur")
    subparsers = parser.add_subparsers(dest="command", required=True)
    owner_parser = subparsers.add_parser("create-owner", help="Créer la première organisation")
    owner_parser.add_argument("--organization-name")
    owner_parser.add_argument("--email")
    arguments = parser.parse_args()

    database_url = os.environ.get("BOOTSTRAP_DATABASE_URL")
    if not database_url:
        print("La variable BOOTSTRAP_DATABASE_URL doit être définie.", file=sys.stderr)
        return 1

    organization_name = _read_value(arguments.organization_name, "Nom de l'organisation : ")
    email = _read_value(arguments.email, "Adresse email : ")
    candidate = getpass("Mot de passe : ")
    confirmation = getpass("Confirmez le mot de passe : ")
    if candidate != confirmation:
        print("Les mots de passe ne correspondent pas.", file=sys.stderr)
        return 1

    try:
        with psycopg.connect(database_url) as connection:
            organization_id = create_owner(connection, organization_name, email, candidate)
    except PasswordPolicyError as error:
        print("\n".join(error.reasons), file=sys.stderr)
        return 1
    except OwnerCreationError as error:
        print(str(error), file=sys.stderr)
        return 1
    except Exception:
        print("La création du compte propriétaire a échoué.", file=sys.stderr)
        return 1

    print(
        f"Identifiant de l'organisation : {organization_id}\n"
        "Renseignez cet identifiant dans OWNER_ORGANIZATION_ID."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
