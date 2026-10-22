"""Validation de la configuration de l'API depuis l'environnement du processus."""

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Paramètres obligatoires fournis par l'environnement."""

    app_env: str = Field(pattern="^(local|test|production)$")
    app_secret_key: SecretStr = Field(min_length=32)
    allowed_origins: str
    database_url: SecretStr
    model_config = SettingsConfigDict(extra="ignore", case_sensitive=False)


def get_settings() -> Settings:
    """Refuse le démarrage si une valeur requise est absente ou invalide."""
    # Pydantic Settings charge les champs requis depuis l'environnement.
    return Settings()  # type: ignore[call-arg]
