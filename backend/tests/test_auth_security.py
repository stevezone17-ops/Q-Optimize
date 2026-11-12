"""Tests for User Authentication, RBAC, Credentials, and Resource Ownership Security (Stage 9.1)."""

import pytest
from httpx import AsyncClient, ASGITransport
from backend.app.main import app
from backend.app.core.security import (
    get_password_hash,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
)
from backend.app.domain.auth.models import UserRole
from backend.app.services.auth_service import AuthService
from backend.app.db.mongodb import db_manager


@pytest.fixture(autouse=True)
def clean_auth_store():
    """Ensure in-memory auth store is clean for predictable test state."""
    db_manager._memory_store["users"] = {}
    db_manager._memory_store["problems"] = {}


@pytest.mark.asyncio
async def test_password_hashing_and_verification():
    """Verify bcrypt salt rounds, secure hashing, and mismatch detection."""
    password = "SecurePassword123!"
    hashed = get_password_hash(password)

    assert hashed != password
    assert hashed.startswith("$2b$")
    assert verify_password(password, hashed) is True
    assert verify_password("WrongPassword!", hashed) is False


@pytest.mark.asyncio
async def test_jwt_token_creation_and_decoding():
    """Verify JWT access and refresh token encoding, claims, and decoding."""
    payload = {"sub": "user-uuid-123", "role": "researcher"}
    token = create_access_token(payload)

    decoded = decode_token(token)
    assert decoded["sub"] == "user-uuid-123"
    assert decoded["role"] == "researcher"
    assert decoded["type"] == "access"
    assert "exp" in decoded
    assert "iat" in decoded


@pytest.mark.asyncio
async def test_user_registration_success():
    """Register new user, verify profile created and password not returned in plain."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.post(
            "/api/v1/auth/register",
            json={
                "email": "alice@example.com",
                "username": "alice",
                "password": "Password123!",
                "full_name": "Alice Quantum",
                "role": "user",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "alice@example.com"
        assert data["username"] == "alice"
        assert data["role"] == "user"
        assert data["is_active"] is True
        assert "password" not in data
        assert "hashed_password" not in data


@pytest.mark.asyncio
async def test_user_registration_duplicate_email_fails():
    """Verify registration fails when email is already in use."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        await ac.post(
            "/api/v1/auth/register",
            json={
                "email": "bob@example.com",
                "username": "bob1",
                "password": "Password123!",
            },
        )
        resp2 = await ac.post(
            "/api/v1/auth/register",
            json={
                "email": "bob@example.com",
                "username": "bob2",
                "password": "Password123!",
            },
        )
        assert resp2.status_code == 400
        assert "already exists" in resp2.json()["detail"]


@pytest.mark.asyncio
async def test_user_registration_weak_password_validation():
    """Verify password strength validation rejects weak passwords."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # Too short
        resp1 = await ac.post(
            "/api/v1/auth/register",
            json={"email": "u1@test.com", "username": "u1", "password": "abc"},
        )
        assert resp1.status_code == 422

        # No digits/special characters
        resp2 = await ac.post(
            "/api/v1/auth/register",
            json={"email": "u2@test.com", "username": "u2", "password": "onlylettershere"},
        )
        assert resp2.status_code == 422


@pytest.mark.asyncio
async def test_user_login_and_token_exchange():
    """Verify login exchanges credentials for access and refresh tokens."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        await ac.post(
            "/api/v1/auth/register",
            json={"email": "charlie@test.com", "username": "charlie", "password": "Password123!"},
        )

        # Login with username
        login_resp = await ac.post(
            "/api/v1/auth/login",
            json={"username_or_email": "charlie", "password": "Password123!"},
        )
        assert login_resp.status_code == 200
        tokens = login_resp.json()
        assert "access_token" in tokens
        assert "refresh_token" in tokens
        assert tokens["token_type"] == "bearer"
        assert tokens["user"]["username"] == "charlie"

        # Login with email
        login_resp_email = await ac.post(
            "/api/v1/auth/login",
            json={"username_or_email": "charlie@test.com", "password": "Password123!"},
        )
        assert login_resp_email.status_code == 200


@pytest.mark.asyncio
async def test_user_login_invalid_credentials():
    """Verify bad credentials return 401."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        await ac.post(
            "/api/v1/auth/register",
            json={"email": "dan@test.com", "username": "dan", "password": "Password123!"},
        )
        resp = await ac.post(
            "/api/v1/auth/login",
            json={"username_or_email": "dan", "password": "WrongPassword999!"},
        )
        assert resp.status_code == 401
        assert "WWW-Authenticate" in resp.headers


@pytest.mark.asyncio
async def test_protected_me_endpoint_authentication():
    """Verify /auth/me requires valid token and rejects unauthorized requests."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # Request without token -> 401
        resp_no_token = await ac.get("/api/v1/auth/me")
        assert resp_no_token.status_code == 401

        # Request with invalid token -> 401
        resp_bad_token = await ac.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer totally_invalid_jwt_token_string"},
        )
        assert resp_bad_token.status_code == 401

        # Register and login to obtain valid token
        await ac.post(
            "/api/v1/auth/register",
            json={"email": "eva@test.com", "username": "eva", "password": "Password123!"},
        )
        login = await ac.post(
            "/api/v1/auth/login",
            json={"username_or_email": "eva", "password": "Password123!"},
        )
        token = login.json()["access_token"]

        # Request with valid token -> 200
        resp_auth = await ac.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp_auth.status_code == 200
        assert resp_auth.json()["username"] == "eva"


@pytest.mark.asyncio
async def test_token_refresh_flow():
    """Verify refresh token can issue new access tokens and invalid token types are rejected."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        await ac.post(
            "/api/v1/auth/register",
            json={"email": "frank@test.com", "username": "frank", "password": "Password123!"},
        )
        login = await ac.post(
            "/api/v1/auth/login",
            json={"username_or_email": "frank", "password": "Password123!"},
        )
        tokens = login.json()
        refresh_token = tokens["refresh_token"]
        access_token = tokens["access_token"]

        # Valid refresh
        refresh_resp = await ac.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token},
        )
        assert refresh_resp.status_code == 200
        new_tokens = refresh_resp.json()
        assert "access_token" in new_tokens

        # Attempting to use access token as refresh token must be rejected
        bad_refresh = await ac.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": access_token},
        )
        assert bad_refresh.status_code == 400


@pytest.mark.asyncio
async def test_password_change_flow():
    """Verify changing password updates hash and allows login with new password."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        await ac.post(
            "/api/v1/auth/register",
            json={"email": "grace@test.com", "username": "grace", "password": "OldPassword123!"},
        )
        login = await ac.post(
            "/api/v1/auth/login",
            json={"username_or_email": "grace", "password": "OldPassword123!"},
        )
        token = login.json()["access_token"]

        # Change password
        change_resp = await ac.post(
            "/api/v1/auth/change-password",
            headers={"Authorization": f"Bearer {token}"},
            json={"old_password": "OldPassword123!", "new_password": "NewPassword2026!"},
        )
        assert change_resp.status_code == 200

        # Login with old password fails
        old_login = await ac.post(
            "/api/v1/auth/login",
            json={"username_or_email": "grace", "password": "OldPassword123!"},
        )
        assert old_login.status_code == 401

        # Login with new password succeeds
        new_login = await ac.post(
            "/api/v1/auth/login",
            json={"username_or_email": "grace", "password": "NewPassword2026!"},
        )
        assert new_login.status_code == 200


@pytest.mark.asyncio
async def test_password_reset_token_flow():
    """Verify token-based forgotten password reset flow."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        await ac.post(
            "/api/v1/auth/register",
            json={"email": "heidi@test.com", "username": "heidi", "password": "InitPassword123!"},
        )

        # Request reset token
        forgot_resp = await ac.post(
            "/api/v1/auth/forgot-password",
            json={"email": "heidi@test.com"},
        )
        assert forgot_resp.status_code == 200
        reset_token = forgot_resp.json()["reset_token"]

        # Confirm reset
        reset_confirm = await ac.post(
            "/api/v1/auth/reset-password",
            json={"token": reset_token, "new_password": "ResetPassword999!"},
        )
        assert reset_confirm.status_code == 200

        # Login with reset password
        login = await ac.post(
            "/api/v1/auth/login",
            json={"username_or_email": "heidi", "password": "ResetPassword999!"},
        )
        assert login.status_code == 200


@pytest.mark.asyncio
async def test_resource_ownership_and_cross_user_isolation():
    """Verify User A cannot delete User B's problem, while an Admin can."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # Register User A (regular user)
        await ac.post(
            "/api/v1/auth/register",
            json={"email": "usera@test.com", "username": "usera", "password": "Password123!", "role": "user"},
        )
        token_a = (await ac.post(
            "/api/v1/auth/login",
            json={"username_or_email": "usera", "password": "Password123!"},
        )).json()["access_token"]

        # Register User B (regular user)
        await ac.post(
            "/api/v1/auth/register",
            json={"email": "userb@test.com", "username": "userb", "password": "Password123!", "role": "user"},
        )
        token_b = (await ac.post(
            "/api/v1/auth/login",
            json={"username_or_email": "userb", "password": "Password123!"},
        )).json()["access_token"]

        # Register Admin User
        await ac.post(
            "/api/v1/auth/register",
            json={"email": "admin@test.com", "username": "adminuser", "password": "Password123!", "role": "admin"},
        )
        token_admin = (await ac.post(
            "/api/v1/auth/login",
            json={"username_or_email": "adminuser", "password": "Password123!"},
        )).json()["access_token"]

        # User A creates a problem
        create_resp = await ac.post(
            "/api/v1/problems",
            headers={"Authorization": f"Bearer {token_a}"},
            json={
                "name": "User A Max-Cut Instance",
                "problem_type": "max_cut",
                "instance": {
                    "nodes": ["Node_1", "Node_2", "Node_3"],
                    "edges": [
                        ["Node_1", "Node_2", 1.0],
                        ["Node_2", "Node_3", 1.0],
                    ],
                },
            },
        )
        assert create_resp.status_code == 201
        problem_id = create_resp.json()["id"]

        # User B attempts to delete User A's problem -> 403 Forbidden
        del_attempt_b = await ac.delete(
            f"/api/v1/problems/{problem_id}",
            headers={"Authorization": f"Bearer {token_b}"},
        )
        assert del_attempt_b.status_code == 403
        assert "permission" in del_attempt_b.json()["detail"].lower()

        # Admin user deletes User A's problem -> 200 OK
        del_admin = await ac.delete(
            f"/api/v1/problems/{problem_id}",
            headers={"Authorization": f"Bearer {token_admin}"},
        )
        assert del_admin.status_code == 200

