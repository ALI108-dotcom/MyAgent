"""Unit and Integration Security Tests for Auth, JWT, RBAC, and Hardening."""

from datetime import datetime, timedelta, timezone

import jwt
import pytest
from fastapi import HTTPException
from httpx import AsyncClient

from app.core.config import Settings, settings
from app.core.middleware import login_rate_limiter
from app.core.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    user_manager,
    validate_password_complexity,
    verify_password,
)
from app.models.auth import UserCreate


def test_password_hashing_and_verification() -> None:
    """Verify bcrypt password hashing and verification."""
    raw = "MySecretPass123!"
    hashed = hash_password(raw)
    assert hashed != raw
    assert verify_password(raw, hashed) is True
    assert verify_password("WrongPass123!", hashed) is False


def test_password_complexity_policy() -> None:
    """Verify password policy enforces length, casing, digits, and special characters."""
    validate_password_complexity("StrongP@ss123")  # Valid

    with pytest.raises(HTTPException) as exc1:
        validate_password_complexity("short1!")
    assert "8 characters" in str(exc1.value.detail)

    with pytest.raises(HTTPException) as exc2:
        validate_password_complexity("lowercase123!")
    assert "uppercase" in str(exc2.value.detail)

    with pytest.raises(HTTPException) as exc3:
        validate_password_complexity("UPPERCASE123!")
    assert "lowercase" in str(exc3.value.detail)

    with pytest.raises(HTTPException) as exc4:
        validate_password_complexity("NoDigitsHere!")
    assert "digit" in str(exc4.value.detail)

    with pytest.raises(HTTPException) as exc5:
        validate_password_complexity("NoSpecial123")
    assert "special character" in str(exc5.value.detail)


def test_jwt_claims_and_issuer_audience_validation() -> None:
    """Verify JWT token encoding, decoding, expiration, issuer, and audience validation."""
    token = create_access_token({"sub": "admin", "role": "admin"})
    assert isinstance(token, str)

    # Valid decode
    decoded = decode_access_token(token)
    assert decoded["sub"] == "admin"
    assert decoded["role"] == "admin"
    assert decoded["iss"] == settings.JWT_ISSUER
    assert decoded["aud"] == settings.JWT_AUDIENCE

    # Expired Token Test
    now = datetime.now(timezone.utc)
    expired_payload = {
        "sub": "admin",
        "exp": int((now - timedelta(minutes=10)).timestamp()),
        "iat": int((now - timedelta(minutes=20)).timestamp()),
        "iss": settings.JWT_ISSUER,
        "aud": settings.JWT_AUDIENCE,
    }
    expired_token = jwt.encode(
        expired_payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM
    )
    with pytest.raises(HTTPException) as exc_exp:
        decode_access_token(expired_token)
    assert "expired" in str(exc_exp.value.detail).lower()

    # Invalid Issuer Test
    bad_iss_payload = {
        "sub": "admin",
        "exp": int((now + timedelta(minutes=10)).timestamp()),
        "iss": "rogue-issuer",
        "aud": settings.JWT_AUDIENCE,
    }
    bad_iss_token = jwt.encode(
        bad_iss_payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM
    )
    with pytest.raises(HTTPException) as exc_iss:
        decode_access_token(bad_iss_token)
    assert "issuer" in str(exc_iss.value.detail).lower()

    # Invalid Audience Test
    bad_aud_payload = {
        "sub": "admin",
        "exp": int((now + timedelta(minutes=10)).timestamp()),
        "iss": settings.JWT_ISSUER,
        "aud": "rogue-audience",
    }
    bad_aud_token = jwt.encode(
        bad_aud_payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM
    )
    with pytest.raises(HTTPException) as exc_aud:
        decode_access_token(bad_aud_token)
    assert "audience" in str(exc_aud.value.detail).lower()

    # Algorithm Confusion 'none' Attack Test
    unsecured_payload = {
        "sub": "admin",
        "exp": int((now + timedelta(minutes=10)).timestamp()),
        "iss": settings.JWT_ISSUER,
        "aud": settings.JWT_AUDIENCE,
    }
    none_token = jwt.encode(unsecured_payload, key="", algorithm="none")
    with pytest.raises(HTTPException):
        decode_access_token(none_token)


def test_production_mode_security_validation() -> None:
    """Verify production mode rejects weak default JWT secrets and wildcard CORS."""
    with pytest.raises(ValueError) as exc:
        Settings(
            ENVIRONMENT="production",
            JWT_SECRET_KEY="dev_secret_key_short",
            CORS_ORIGINS=["http://localhost:3000"],
        )
    assert "JWT_SECRET_KEY must be a secure random secret" in str(exc.value)

    with pytest.raises(ValueError) as exc_cors:
        Settings(
            ENVIRONMENT="production",
            JWT_SECRET_KEY="a_very_long_secure_random_production_secret_key_123456789",
            CORS_ORIGINS=["*"],
        )
    assert "CORS_ORIGINS must not contain '*'" in str(exc_cors.value)


@pytest.mark.asyncio
async def test_auth_api_endpoints_and_cookie_support(async_client: AsyncClient) -> None:
    """Test user registration, login, cookie setting, protected endpoints, and RBAC."""
    # 1. Register new user
    reg_req = {
        "username": "testuser_hardened",
        "email": "testuser_hardened@agentai.dev",
        "password": "Password123!",
        "role": "user",
    }
    reg_resp = await async_client.post("/api/v1/auth/register", json=reg_req)
    assert reg_resp.status_code == 201
    user_data = reg_resp.json()
    assert user_data["username"] == "testuser_hardened"
    assert "password_hash" not in user_data

    # 2. Login valid credentials and verify HttpOnly cookie
    login_resp = await async_client.post(
        "/api/v1/auth/login",
        json={"username": "testuser_hardened", "password": "Password123!"},
    )
    assert login_resp.status_code == 200
    token_data = login_resp.json()
    user_token = token_data["access_token"]
    assert token_data["token_type"] == "bearer"
    assert "agentai_access_token" in login_resp.cookies

    # 3. Non-enumerating login errors
    bad_pass_resp = await async_client.post(
        "/api/v1/auth/login",
        json={"username": "testuser_hardened", "password": "WrongPassword!"},
    )
    assert bad_pass_resp.status_code == 401
    assert bad_pass_resp.json()["detail"] == "Invalid username or password."

    unknown_user_resp = await async_client.post(
        "/api/v1/auth/login",
        json={"username": "unknown_user_xyz", "password": "Password123!"},
    )
    assert unknown_user_resp.status_code == 401
    assert unknown_user_resp.json()["detail"] == "Invalid username or password."

    # 4. Access protected endpoint WITHOUT auth header or cookie -> 401
    async_client.cookies.clear()
    unauth_resp = await async_client.post(
        "/api/v1/agent/llm/generate",
        json={"prompt": "hello", "provider": "mock"},
    )
    assert unauth_resp.status_code == 401

    # 5. Access protected endpoint WITH valid Bearer header -> 200
    user_headers = {"Authorization": f"Bearer {user_token}"}
    auth_llm_resp = await async_client.post(
        "/api/v1/agent/llm/generate",
        json={"prompt": "hello", "provider": "mock"},
        headers=user_headers,
    )
    assert auth_llm_resp.status_code == 200

    # 6. USER role accessing ADMIN-only endpoint (/rag/index) -> 403 Forbidden
    user_admin_resp = await async_client.post(
        "/api/v1/agent/rag/index",
        headers=user_headers,
    )
    assert user_admin_resp.status_code == 403

    # 7. Login admin user and access ADMIN-only endpoint -> 200
    admin_login_resp = await async_client.post(
        "/api/v1/auth/login",
        json={"username": "admin", "password": "AdminPass123!"},
    )
    assert admin_login_resp.status_code == 200
    admin_token = admin_login_resp.json()["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    admin_rag_resp = await async_client.post(
        "/api/v1/agent/rag/index",
        headers=admin_headers,
    )
    assert admin_rag_resp.status_code == 200


@pytest.mark.asyncio
async def test_user_data_isolation(async_client: AsyncClient) -> None:
    """Test user session data isolation (User A cannot access User B's session memory)."""
    # User A login
    login_a = await async_client.post(
        "/api/v1/auth/login",
        json={"username": "user", "password": "UserPass123!"},
    )
    headers_a = {"Authorization": f"Bearer {login_a.json()['access_token']}"}

    # User A creates a session
    s_a_resp = await async_client.post(
        "/api/v1/agent/memory/sessions",
        json={"title": "User A Private Session"},
        headers=headers_a,
    )
    assert s_a_resp.status_code == 201
    s_a_id = s_a_resp.json()["session_id"]

    # Register & Login User B
    await user_manager.create_user(
        UserCreate(username="user_b", email="b@agentai.dev", password="Password123!")
    )
    login_b = await async_client.post(
        "/api/v1/auth/login",
        json={"username": "user_b", "password": "Password123!"},
    )
    headers_b = {"Authorization": f"Bearer {login_b.json()['access_token']}"}

    # User B tries to access User A's session -> 403 Forbidden
    b_access_a = await async_client.get(
        f"/api/v1/agent/memory/sessions/{s_a_id}",
        headers=headers_b,
    )
    assert b_access_a.status_code == 403

    # Admin accesses User A's session -> 200 OK
    login_admin = await async_client.post(
        "/api/v1/auth/login",
        json={"username": "admin", "password": "AdminPass123!"},
    )
    headers_admin = {"Authorization": f"Bearer {login_admin.json()['access_token']}"}
    admin_access_a = await async_client.get(
        f"/api/v1/agent/memory/sessions/{s_a_id}",
        headers=headers_admin,
    )
    assert admin_access_a.status_code == 200


@pytest.mark.asyncio
async def test_security_headers(async_client: AsyncClient) -> None:
    """Verify modern security headers injected into API responses."""
    response = await async_client.get("/api/v1/health")
    assert response.status_code == 200
    headers = response.headers
    assert headers["X-Content-Type-Options"] == "nosniff"
    assert headers["X-Frame-Options"] == "DENY"
    assert "Strict-Transport-Security" in headers
    assert "Referrer-Policy" in headers
    assert "Permissions-Policy" in headers
    assert "Content-Security-Policy" in headers


def test_rate_limiter() -> None:
    """Verify rate limiter blocks brute force attempts after threshold."""
    key = "test_ip_127_0_0_1_hardening"
    for _ in range(login_rate_limiter.max_requests):
        login_rate_limiter.check_rate_limit(key)

    with pytest.raises(Exception) as exc_info:
        login_rate_limiter.check_rate_limit(key)
    assert "Rate limit exceeded" in str(exc_info.value)
