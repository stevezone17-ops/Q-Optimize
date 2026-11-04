"""Tests for application settings and configuration."""

from backend.app.core.config import Settings


def test_default_settings():
    cfg = Settings()
    assert cfg.APP_ENV in ["development", "test", "production"]
    assert cfg.API_V1_PREFIX == "/api/v1"
    assert "http://localhost:5173" in cfg.FRONTEND_ORIGIN
