"""Tests for application settings, secrets validation, and environment isolation."""

import pytest
from backend.app.core.config import Settings


def test_default_settings():
    cfg = Settings()
    assert cfg.APP_ENV in ["development", "test", "production"]
    assert cfg.API_V1_PREFIX == "/api/v1"
    assert "http://localhost:5173" in cfg.FRONTEND_ORIGIN


def test_production_rejects_debug_mode():
    """Verify production environment strictly rejects DEBUG=True."""
    with pytest.raises(ValueError, match="DEBUG mode must be disabled"):
        Settings(
            APP_ENV="production",
            DEBUG=True,
            JWT_SECRET_KEY="a" * 32,
        )


def test_production_rejects_weak_or_default_jwt_secret():
    """Verify production environment rejects default insecure JWT secret or short secrets."""
    with pytest.raises(ValueError, match="cryptographically strong secret"):
        Settings(
            APP_ENV="production",
            DEBUG=False,
            JWT_SECRET_KEY="insecure_dev_secret_replace_in_production",
        )

    with pytest.raises(ValueError, match="cryptographically strong secret"):
        Settings(
            APP_ENV="production",
            DEBUG=False,
            JWT_SECRET_KEY="short-secret",
        )


def test_production_accepts_hardened_settings():
    """Verify production environment succeeds with valid secrets and production flags."""
    cfg = Settings(
        APP_ENV="production",
        DEBUG=False,
        JWT_SECRET_KEY="production-super-secret-key-32-chars-long!",
    )
    assert cfg.APP_ENV == "production"
    assert cfg.DEBUG is False
    assert len(cfg.JWT_SECRET_KEY) >= 32
