"""Vérifie le hachage et la politique des mots de passe."""

import pytest
from argon2 import PasswordHasher

from guetteur import security
from guetteur.security import passwords


def _candidate() -> str:
    """Construit une valeur synthétique pour les tests."""
    return "silver" + "harbor" + "2026"


def test_hash_uses_configured_argon2id_parameters() -> None:
    candidate = _candidate()
    stored_hash = passwords.hash_password(candidate)
    hash_parts = stored_hash.split("$")
    algorithm, parameters = hash_parts[1], hash_parts[3]
    parameter_values = dict(part.split("=") for part in parameters.split(","))
    valid_parameters = (
        algorithm == "argon2id"
        and parameter_values == {"m": "19456", "t": "2", "p": "1"}
    )
    assert valid_parameters, "Les paramètres Argon2id produits ne correspondent pas à la décision."
    assert passwords.verify_password(stored_hash, candidate)


def test_verification_rejects_different_and_invalid_values() -> None:
    candidate = _candidate()
    stored_hash = passwords.hash_password(candidate)
    wrong_candidate = "copper" + "meadow" + "2026"

    assert not passwords.verify_password(stored_hash, wrong_candidate)
    assert not passwords.verify_password("empreinte invalide", candidate)
    assert not passwords.verify_password("\u2603", candidate)


def test_password_needs_rehash_for_weaker_parameters() -> None:
    weak_hasher = PasswordHasher(
        time_cost=1,
        memory_cost=8,
        parallelism=1,
        hash_len=passwords.ARGON2_HASH_LEN,
        salt_len=passwords.ARGON2_SALT_LEN,
    )
    old_hash = weak_hasher.hash(_candidate())

    assert passwords.password_needs_rehash(old_hash)


def test_nfkc_normalization_is_applied_before_verification() -> None:
    candidate = "Orbit" + "\ufb03" + "Harbor2026"
    normalized_candidate = passwords.normalize_password(candidate)
    stored_hash = passwords.hash_password(normalized_candidate)
    normalization_changed_value = normalized_candidate != candidate

    assert normalization_changed_value, (
        "La normalisation NFKC doit modifier la ligature de compatibilité."
    )
    assert passwords.verify_password(stored_hash, candidate)


@pytest.mark.parametrize(
    ("candidate", "email", "expected_reason"),
    [
        ("a" * 11, "owner@example.test", "12 et 128"),
        ("x" * 129, "owner@example.test", "12 et 128"),
        ("Alice" + "Harbor2026", "alice@example.test", "partie locale"),
        ("password" + "123456", "owner@example.test", "moins courant"),
        ("a" * 12, "owner@example.test", "répétitions"),
        ("abcdefghijkl", "owner@example.test", "répétitions"),
        ("123456789012", "owner@example.test", "répétitions"),
    ],
    ids=(
        "court",
        "long",
        "partie-locale-email",
        "liste-courante",
        "repetition",
        "suite-lettres",
        "suite-chiffres",
    ),
)
def test_password_policy_rejects_weak_candidates(
    candidate: str, email: str, expected_reason: str
) -> None:
    reasons = passwords.validate_password_policy(candidate, email)

    expected_refusal = any(expected_reason in reason for reason in reasons)
    no_candidate_disclosure = all(candidate not in reason for reason in reasons)
    assert expected_refusal
    assert no_candidate_disclosure, "Un motif de refus ne doit pas reprendre la valeur testée."


def test_password_policy_accepts_a_synthetic_candidate() -> None:
    reasons = passwords.validate_password_policy(_candidate(), "owner@example.test")

    assert reasons == []


def test_common_password_file_is_loaded_only_once(monkeypatch: pytest.MonkeyPatch) -> None:
    original_files = passwords.files
    load_count = 0

    def counted_files(package: str):
        nonlocal load_count
        load_count += 1
        return original_files(package)

    passwords._load_common_passwords.cache_clear()
    monkeypatch.setattr(passwords, "files", counted_files)
    passwords.validate_password_policy(_candidate(), "owner@example.test")
    passwords.validate_password_policy(_candidate(), "owner@example.test")
    passwords._load_common_passwords.cache_clear()

    assert load_count == 1


def test_missing_account_path_performs_a_dummy_verification(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = 0

    def record_verification(stored_hash: str, candidate: str) -> bool:
        nonlocal calls
        del stored_hash, candidate
        calls += 1
        return True

    monkeypatch.setattr(passwords, "_verify_hash", record_verification)
    result = passwords.verify_password_or_dummy(None, _candidate())

    assert result is False
    assert calls == 1


def test_module_exports_the_argon2_parameters() -> None:
    exported_values = (
        passwords.ARGON2_TIME_COST,
        passwords.ARGON2_MEMORY_COST,
        passwords.ARGON2_PARALLELISM,
        passwords.ARGON2_HASH_LEN,
        passwords.ARGON2_SALT_LEN,
    )

    assert exported_values == (2, 19_456, 1, 32, 16)
    assert security.passwords is passwords
