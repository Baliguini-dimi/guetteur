"""Hachage Argon2id et règles de choix des mots de passe."""

import secrets
import unicodedata
from functools import lru_cache
from importlib.resources import files
from itertools import pairwise

from argon2 import PasswordHasher

ARGON2_TIME_COST = 2
ARGON2_MEMORY_COST = 19_456
ARGON2_PARALLELISM = 1
ARGON2_HASH_LEN = 32
ARGON2_SALT_LEN = 16

PASSWORD_HASHER = PasswordHasher(
    time_cost=ARGON2_TIME_COST,
    memory_cost=ARGON2_MEMORY_COST,
    parallelism=ARGON2_PARALLELISM,
    hash_len=ARGON2_HASH_LEN,
    salt_len=ARGON2_SALT_LEN,
)


def normalize_password(password: str) -> str:
    """Normalise un mot de passe en Unicode NFKC sans autre transformation."""
    return unicodedata.normalize("NFKC", password)


@lru_cache(maxsize=1)
def _load_common_passwords() -> frozenset[str]:
    """Charge une seule fois la liste locale incluse dans le paquet."""
    content = files("guetteur.security").joinpath("common_passwords.txt").read_text(
        encoding="utf-8"
    )
    return frozenset(line.strip() for line in content.splitlines() if line.strip())


@lru_cache(maxsize=1)
def _dummy_password_hash() -> str:
    """Calcule une fois une empreinte factice avec les paramètres courants."""
    return PASSWORD_HASHER.hash(secrets.token_urlsafe(32))


def _is_trivial_sequence(candidate: str) -> bool:
    """Détecte les répétitions et suites simples après retrait des espaces."""
    compact = "".join(candidate.casefold().split())
    if len(compact) < 12:
        return False
    if len(set(compact)) == 1:
        return True

    sequences = (
        "abcdefghijklmnopqrstuvwxyz",
        "zyxwvutsrqponmlkjihgfedcba",
        "0123456789",
        "9876543210",
        "qwertyuiop",
        "asdfghjkl",
        "zxcvbnm",
        "azertyuiop",
        "qsdfghjklm",
        "wxcvbn",
    )
    for sequence in sequences:
        repeated = sequence + sequence
        if any(compact in repeated[start : start + len(compact)] for start in range(len(sequence))):
            return True

    differences = [ord(right) - ord(left) for left, right in pairwise(compact)]
    return bool(differences) and all(step == differences[0] for step in differences) and abs(
        differences[0]
    ) == 1


def validate_password_policy(password: str, email: str) -> list[str]:
    """Retourne les motifs de refus sans reprendre le mot de passe."""
    normalized = normalize_password(password)
    reasons: list[str] = []

    if not 12 <= len(normalized) <= 128:
        reasons.append("Le mot de passe doit contenir entre 12 et 128 caractères.")

    local_part = email.split("@", maxsplit=1)[0].casefold()
    if len(local_part) >= 3 and local_part in normalized.casefold():
        reasons.append("Le mot de passe ne doit pas contenir la partie locale de l'adresse email.")

    compact = "".join(normalized.casefold().split())
    if compact in _load_common_passwords():
        reasons.append("Choisissez un mot de passe moins courant.")

    if _is_trivial_sequence(normalized):
        reasons.append("Évitez les répétitions et les suites faciles à deviner.")

    return reasons


def hash_password(password: str) -> str:
    """Normalise puis calcule une empreinte Argon2id."""
    return PASSWORD_HASHER.hash(normalize_password(password))


def _verify_hash(stored_hash: str, normalized_password: str) -> bool:
    """Délègue la vérification afin de permettre son simulation dans les tests."""
    return PASSWORD_HASHER.verify(stored_hash, normalized_password)


def verify_password(stored_hash: str, password: str) -> bool:
    """Vérifie un mot de passe sans exposer les erreurs d'empreinte."""
    try:
        return _verify_hash(stored_hash, normalize_password(password))
    except Exception:
        return False


def password_needs_rehash(stored_hash: str) -> bool:
    """Indique si une empreinte doit être recalculée avec les paramètres courants."""
    try:
        return PASSWORD_HASHER.check_needs_rehash(stored_hash)
    except Exception:
        return True


def verify_password_or_dummy(stored_hash: str | None, password: str) -> bool:
    """Vérifie toujours une empreinte, même si le compte n'existe pas."""
    if stored_hash is None:
        verify_password(_dummy_password_hash(), password)
        return False
    return verify_password(stored_hash, password)
