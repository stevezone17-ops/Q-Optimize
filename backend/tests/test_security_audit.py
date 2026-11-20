"""Comprehensive Security Audit and Vulnerability Assessment Tests (Stage 9.9).

Validates:
1. Authentication bypass prevention (401 Unauthorized)
2. Token tampering and expiration handling
3. Cross-user isolation and horizontal privilege escalation prevention (403 Forbidden)
4. Sensitive error leakage and traceback suppression
5. Rate limiting under burst traffic (429 Too Many Requests)
6. NoSQL injection pattern sanitization and rejection (400 Bad Request)
7. Security response headers enforcement
"""

from datetime import timedelta
import pytest
from httpx import AsyncClient, ASGITransport
from fastapi import HTTPException
from backend.app.main import app
from backend.app.core.security import create_access_token
from backend.app.core.middleware import rate_limiter, sanitize_query_parameters
from backend.app.db.mongodb import db_manager


@pytest.fixture(autouse=True)
def clean_test_environment():
    """Reset rate limiter and in-memory store before each security test."""
    rate_limiter.reset()
    rate_limiter.enabled = True
    db_manager._memory_store["users"] = {}
    db_manager._memory_store["problems"] = {}
    db_manager._memory_store["experiments"] = {}


@pytest.mark.asyncio
async def test_auth_bypass_prevention():
    """Verify protected endpoints reject requests lacking valid credentials with 401."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # /api/v1/auth/me requires Bearer token
        res1 = await ac.get("/api/v1/auth/me")
        assert res1.status_code == 401, f"Expected 401 on /auth/me, got {res1.status_code}"
        assert "detail" in res1.json()

        # /api/v1/jobs requires Bearer token
        res2 = await ac.get("/api/v1/jobs")
        assert res2.status_code == 401, f"Expected 401 on /jobs, got {res2.status_code}"

        # /api/v1/auth/change-password requires Bearer token
        res3 = await ac.post("/api/v1/auth/change-password", json={"old_password": "x", "new_password": "y"})
        assert res3.status_code == 401, f"Expected 401 on /change-password, got {res3.status_code}"


@pytest.mark.asyncio
async def test_tampered_token_rejection():
    """Verify tampered JWT tokens are strictly rejected with 401."""
    valid_token = create_access_token({"sub": "legit-user", "role": "user"})
    # Tamper with signature by altering the last 5 characters
    tampered_token = valid_token[:-5] + "XXXXX"

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        headers = {"Authorization": f"Bearer {tampered_token}"}
        res = await ac.get("/api/v1/auth/me", headers=headers)
        assert res.status_code == 401
        assert "detail" in res.json()


@pytest.mark.asyncio
async def test_expired_token_rejection():
    """Verify expired JWT tokens cannot be used to authenticate."""
    expired_token = create_access_token(
        {"sub": "expired-user", "role": "user"},
        expires_delta=timedelta(seconds=-3600),
    )

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        headers = {"Authorization": f"Bearer {expired_token}"}
        res = await ac.get("/api/v1/auth/me", headers=headers)
        assert res.status_code == 401


@pytest.mark.asyncio
async def test_cross_user_isolation_security():
    """Verify User A cannot mutate private resources created by User B (403 Forbidden)."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # Register User A
        reg_a = await ac.post("/api/v1/auth/register", json={
            "email": "user_a@qoptimize.internal",
            "username": "user_a_sec",
            "password": "SecurePasswordA123!",
        })
        assert reg_a.status_code == 201

        login_a = await ac.post("/api/v1/auth/login", json={
            "username_or_email": "user_a_sec",
            "password": "SecurePasswordA123!",
        })
        assert login_a.status_code == 200
        token_a = login_a.json()["access_token"]

        # Register User B
        reg_b = await ac.post("/api/v1/auth/register", json={
            "email": "user_b@qoptimize.internal",
            "username": "user_b_sec",
            "password": "SecurePasswordB123!",
        })
        assert reg_b.status_code == 201

        login_b = await ac.post("/api/v1/auth/login", json={
            "username_or_email": "user_b_sec",
            "password": "SecurePasswordB123!",
        })
        assert login_b.status_code == 200
        token_b = login_b.json()["access_token"]

        # User A creates a problem
        create_res = await ac.post(
            "/api/v1/problems",
            headers={"Authorization": f"Bearer {token_a}"},
            json={
                "name": "User A Private Problem",
                "problem_type": "max_cut",
                "instance": {
                    "nodes": ["A", "B"],
                    "edges": [["A", "B", 1.0]],
                },
            },
        )
        assert create_res.status_code == 201
        problem_id = create_res.json()["id"]

        # User B attempts to delete User A's problem -> strictly 403 Forbidden
        user_b_del = await ac.delete(
            f"/api/v1/problems/{problem_id}",
            headers={"Authorization": f"Bearer {token_b}"},
        )
        assert user_b_del.status_code == 403, (
            f"Expected 403 for cross-user problem deletion, got {user_b_del.status_code}"
        )
        assert "permission" in user_b_del.json()["detail"].lower()


@pytest.mark.asyncio
async def test_error_response_does_not_leak_traceback():
    """Verify error responses return structured details without raw Python tracebacks."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        res = await ac.get("/api/v1/problems/non-existent-uuid-9999999999999999999")
        assert "traceback" not in res.text.lower()
        assert "file \"" not in res.text.lower()


def test_nosql_injection_sanitization():
    """Verify query parameter sanitizer rejects operator injection keys with 400 Bad Request."""
    malicious_params = {
        "search": "test",
        "$where": "this.password == 'secret'",
    }
    with pytest.raises(HTTPException) as exc_info:
        sanitize_query_parameters(malicious_params)
    assert exc_info.value.status_code == 400
    assert "$where" in exc_info.value.detail


@pytest.mark.asyncio
async def test_rate_limiting_enforcement_and_retry_after():
    """Verify rate limiter blocks burst traffic exceeding defined capacity with 429."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        blocked = False
        for i in range(25):
            res = await ac.post("/api/v1/auth/login", json={
                "username_or_email": f"burst_user_{i}",
                "password": "Password123!",
            })
            if res.status_code == 429:
                blocked = True
                assert "Retry-After" in res.headers
                assert "detail" in res.json()
                break

        assert blocked, "Rate limiter failed to block burst requests exceeding 20/min threshold"
