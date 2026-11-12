"""Tests for API Security, Headers, Rate Limiting, Size Limits, and Quotas (Stage 9.2)."""

import pytest
from httpx import AsyncClient, ASGITransport
from backend.app.main import app
from backend.app.core.middleware import (
    rate_limiter,
    sanitize_query_parameters,
    enforce_quantum_quotas,
)
from fastapi import HTTPException


@pytest.fixture(autouse=True)
def reset_rate_limiter_state():
    """Reset rate limiter state before each test."""
    rate_limiter.reset()
    rate_limiter.enabled = True


@pytest.mark.asyncio
async def test_security_headers_present():
    """Verify standard security headers are applied to all API responses."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/health")
        assert response.status_code == 200
        headers = response.headers
        assert headers.get("X-Content-Type-Options") == "nosniff"
        assert headers.get("X-Frame-Options") == "DENY"
        assert headers.get("X-XSS-Protection") == "1; mode=block"
        assert "max-age=31536000" in headers.get("Strict-Transport-Security", "")
        assert headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"
        assert "default-src 'self'" in headers.get("Content-Security-Policy", "")
        assert "geolocation=()" in headers.get("Permissions-Policy", "")


@pytest.mark.asyncio
async def test_payload_size_limit_rejection():
    """Verify request exceeding 10MB payload size limit is rejected with 413."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # Simulate payload over 10MB using Content-Length header
        huge_length = str(15 * 1024 * 1024)
        response = await ac.post(
            "/api/v1/problems",
            headers={"Content-Length": huge_length, "Content-Type": "application/json"},
            content=b'{"name": "oversized"}',
        )
        assert response.status_code == 413
        assert "10MB" in response.json()["detail"]


@pytest.mark.asyncio
async def test_rate_limiter_exceeded_triggers_429():
    """Verify exceeding rate limit quota returns 429 Too Many Requests with Retry-After header."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # Auth quota is 20 req/min
        exceeded = False
        for i in range(25):
            res = await ac.post(
                "/api/v1/auth/login",
                json={"username_or_email": f"user_{i}", "password": "WrongPassword123!"},
            )
            if res.status_code == 429:
                exceeded = True
                assert "Retry-After" in res.headers
                assert "Rate limit exceeded" in res.json()["detail"]
                break
        assert exceeded is True


@pytest.mark.asyncio
async def test_quantum_qubit_quota_enforcement():
    """Verify circuit requiring > 20 qubits triggers quota exceeded error."""
    with pytest.raises(HTTPException) as exc_info:
        enforce_quantum_quotas(num_qubits=25, p_depth=1)
    assert exc_info.value.status_code == 400
    assert "20 qubits" in exc_info.value.detail


@pytest.mark.asyncio
async def test_quantum_depth_quota_enforcement():
    """Verify QAOA depth p > 10 triggers quota exceeded error."""
    with pytest.raises(HTTPException) as exc_info:
        enforce_quantum_quotas(num_qubits=4, p_depth=12)
    assert exc_info.value.status_code == 400
    assert "p=12" in exc_info.value.detail


@pytest.mark.asyncio
async def test_quantum_evaluation_budget_enforcement():
    """Verify evaluation iterations > 500 triggers quota error."""
    with pytest.raises(HTTPException) as exc_info:
        enforce_quantum_quotas(num_qubits=4, p_depth=1, max_evaluations=1000)
    assert exc_info.value.status_code == 400
    assert "500" in exc_info.value.detail


def test_nosql_injection_sanitization():
    """Verify special operator keys starting with $ or containing . are rejected."""
    malicious_query = {
        "user": "alice",
        "$where": "this.password == 'secret'",
    }
    with pytest.raises(HTTPException) as exc_info:
        sanitize_query_parameters(malicious_query)
    assert exc_info.value.status_code == 400
    assert "prohibited" in exc_info.value.detail

    dotted_query = {
        "profile.admin": True,
    }
    with pytest.raises(HTTPException) as exc_info2:
        sanitize_query_parameters(dotted_query)
    assert exc_info2.value.status_code == 400

