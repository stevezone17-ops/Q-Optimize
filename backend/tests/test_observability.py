"""Tests for Logging, Observability, Health Checks, and Sensitive Data Redaction (Stage 9.6)."""

import logging
from backend.app.core.logging import SensitiveDataRedactor


def test_liveness_endpoints(client):
    """Verify Kubernetes liveness probe returns HTTP 200 and alive state."""
    res_root = client.get("/health/live")
    assert res_root.status_code == 200
    assert res_root.json()["status"] == "live"

    res_v1 = client.get("/api/v1/health/live")
    assert res_v1.status_code == 200
    assert res_v1.json()["status"] == "live"


def test_readiness_endpoints(client):
    """Verify Kubernetes readiness probe returns HTTP 200 and database/resource health."""
    res_root = client.get("/health/ready")
    assert res_root.status_code == 200
    assert res_root.json()["status"] == "ready"

    res_v1 = client.get("/api/v1/health/ready")
    assert res_v1.status_code == 200
    assert res_v1.json()["status"] == "ready"
    assert "database_connected" in res_v1.json()


def test_health_detailed_observability_metrics(client):
    """Verify /api/v1/health provides genuine workers and system telemetry."""
    res = client.get("/api/v1/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy"
    assert "workers" in data
    assert "total_tracked_jobs" in data["workers"]
    assert "dead_letter_count" in data["workers"]
    assert "system" in data
    assert "memory_percent" in data["system"]
    assert isinstance(data["system"]["memory_percent"], (int, float))


def test_sensitive_data_redactor_filter():
    """Verify sensitive password and bearer token redaction from log streams."""
    redactor = SensitiveDataRedactor()

    # Test password redaction
    record_pw = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname="",
        lineno=0,
        msg='User authentication attempt: password="MySecretPassword123!" for user john',
        args=(),
        exc_info=None,
    )
    redactor.filter(record_pw)
    assert "MySecretPassword123!" not in record_pw.msg
    assert "[REDACTED]" in record_pw.msg

    # Test Bearer token redaction
    record_jwt = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname="",
        lineno=0,
        msg="Inbound authorization header: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.xyz123",
        args=(),
        exc_info=None,
    )
    redactor.filter(record_jwt)
    assert "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.xyz123" not in record_jwt.msg
    assert "[REDACTED]" in record_jwt.msg
