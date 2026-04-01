import pytest
from unittest.mock import AsyncMock, patch
from httpx import AsyncClient, ASGITransport
from app.api.dependencies import get_db
from app.main import app


# 1. Mock the Google Verification Service
@pytest.fixture
def mock_google_verify(monkeypatch):
    def mock_return(token):
        return {
            "sub": "test-google-id-123",
            "email": "test@example.com",
            "email_verified": True,
        }

    monkeypatch.setattr("app.api.v1.auth.verify_google_token", mock_return)


@pytest.mark.asyncio
async def test_google_login_flow():
    # Mock verify_google_token to return a success object
    async def mock_verify(token):
        return {
            "sub": "123456789",
            "email": "test@autopedicare.com",
            "email_verified": True,
        }

    with patch("app.api.v1.auth.verify_google_token", new_callable=AsyncMock) as mock:
        mock.side_effect = mock_verify

        # Setup Transport
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            # We send a dummy token; the mock will intercept it anyway
            payload = {"token": "valid_mock_token"}

            # Call the endpoint
            response = await ac.post(
                "/api/v1/auth/google",
                json=payload,
                headers={"X-Forwarded-For": "1.1.1.1"},  # Speeds up middleware
            )

            # Check results
            assert response.status_code == 200
            data = response.json()
            assert "access_token" in data
            assert "refresh_token" in data


@pytest.mark.asyncio
async def test_middleware_rejection_logic():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        response = await ac.get("/debug-middleware")
        assert response.status_code == 200
        body = response.json()
        assert "request_id" in body
        assert "ip" in body
        assert "device" in body


@pytest.mark.asyncio
async def test_apple_login_flow():
    # Mock Apple verification
    async def mock_verify(token):
        return {
            "sub": "apple-123456",
            "email": "apple@example.com",
            "email_verified": True,
        }

    with patch("app.api.v1.auth.verify_apple_token", new_callable=AsyncMock) as mock:
        mock.side_effect = mock_verify

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            payload = {"token": "valid_apple_token"}
            response = await ac.post("/api/v1/auth/apple", json=payload)

            assert response.status_code == 200
            data = response.json()
            assert "access_token" in data
            assert data["user"]["email"] == "apple@example.com"


@pytest.mark.asyncio
async def test_token_refresh_flow():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # 1. First get tokens from a login (we'll just mock google for this)
        # However, to be cleaner, we can manually generate a refresh token
        from app.core.security import create_refresh_token

        refresh_token = create_refresh_token({"sub": "user-123"})

        # 2. Call refresh
        payload = {"refresh_token": refresh_token}
        response = await ac.post("/api/v1/auth/refresh", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data


@pytest.mark.asyncio
async def test_google_login_invalid_token(monkeypatch):
    from fastapi import HTTPException

    async def mock_verify_fail(token):
        raise HTTPException(status_code=401, detail="Google token verification failed")

    monkeypatch.setattr("app.api.v1.auth.verify_google_token", mock_verify_fail)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.post("/api/v1/auth/google", json={"token": "invalid_token"})
        assert response.status_code == 401


# @pytest.mark.asyncio
# async def test_google_login_rate_limit(monkeypatch):
#     async def mock_verify(token):
#         return {
#             "sub": "123456789",
#             "email": "test@autopedicare.com",
#             "email_verified": True,
#         }

#     monkeypatch.setattr("app.api.v1.auth.verify_google_token", mock_verify)

#     transport = ASGITransport(app=app)
#     async with AsyncClient(transport=transport, base_url="http://test") as ac:
#         payload = {"token": "valid_mock_token"}
#         headers = {"X-Forwarded-For": "2.2.2.2"}

#         for _ in range(5):
#             r = await ac.post("/api/v1/auth/google", json=payload, headers=headers)
#             assert r.status_code == 200

#         r = await ac.post("/api/v1/auth/google", json=payload, headers=headers)
#         assert r.status_code == 429


@pytest.mark.asyncio
async def test_expired_access_token_is_rejected():
    from datetime import datetime, timedelta, timezone
    from app.core.config import settings
    from jose import jwt

    expired_token = jwt.encode(
        {
            "sub": "user-123",
            "type": "access",
            "exp": datetime.now(timezone.utc) - timedelta(seconds=1),
        },
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get(
            "/api/v1/vehicles",
            headers={"Authorization": f"Bearer {expired_token}"},
        )
        assert response.status_code == 401


@pytest.mark.asyncio
async def test_invalid_access_token_is_rejected():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get(
            "/api/v1/vehicles",
            headers={"Authorization": "Bearer invalid.token.here"},
        )
        assert response.status_code == 401


@pytest.mark.asyncio
async def test_health_endpoints():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        r1 = await ac.get("/health/live")
        r2 = await ac.get("/health/ready")
        assert r1.status_code == 200
        assert r2.status_code == 200
        assert r1.json()["status"] == "alive"
        assert r2.json()["status"] == "ready"
