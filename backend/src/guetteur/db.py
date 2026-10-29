"""Fonctions d'accès au contexte d'organisation PostgreSQL."""

from typing import Protocol
from uuid import UUID


class _Cursor(Protocol):
    """Interface minimale du curseur PostgreSQL utilisé ici."""

    def execute(self, query: str, parameters: tuple[str, ...]) -> object: ...


def set_organization_context(cursor: _Cursor, organization_id: UUID) -> None:
    """Fixe le contexte pour la transaction courante uniquement."""
    if not isinstance(organization_id, UUID):
        raise TypeError("organization_id doit être un uuid.UUID")
    cursor.execute("SELECT set_config('app.organization_id', %s, true)", (str(organization_id),))
