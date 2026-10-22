"""Prépare une configuration synthétique avant le chargement de l'application."""

import os
import secrets

os.environ["APP_SECRET_KEY"] = secrets.token_hex(32)
os.environ["DATABASE_URL"] = (
    f"postgresql://test_user:{secrets.token_hex(24)}@localhost/test_db"
)
os.environ["APP_ENV"] = "test"
os.environ["ALLOWED_ORIGINS"] = "http://testserver"
