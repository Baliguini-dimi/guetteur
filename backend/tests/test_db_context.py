"""Vérifie la pose du contexte d'organisation PostgreSQL."""

from uuid import uuid4

import pytest

from guetteur.db import set_organization_context


class FakeCursor:
    """Curseur de test qui mémorise la dernière requête exécutée."""

    def __init__(self) -> None:
        self.query: str | None = None
        self.parameters: tuple[str, ...] | None = None

    def execute(self, query: str, parameters: tuple[str, ...]) -> None:
        """Enregistre la requête et ses paramètres."""
        self.query = query
        self.parameters = parameters


def test_sets_transaction_local_organization_context() -> None:
    """La fonction transmet l'UUID comme paramètre et limite sa portée à la transaction."""
    cursor = FakeCursor()
    organization_id = uuid4()

    set_organization_context(cursor, organization_id)

    assert cursor.query == "SELECT set_config('app.organization_id', %s, true)"
    assert cursor.parameters == (str(organization_id),)


def test_rejects_non_uuid_organization_id() -> None:
    """Une valeur qui n'est pas un UUID est refusée avant l'exécution."""
    cursor = FakeCursor()
    with pytest.raises(TypeError, match="uuid.UUID"):
        set_organization_context(cursor, "not-a-uuid")  # type: ignore[arg-type]
    assert cursor.query is None
