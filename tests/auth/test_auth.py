import pytest
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
@pytest.mark.asyncio
async def test_google_login_flow(monkeypatch):
    # 1. THE MOCK: Force the service to return a success object
    async def mock_verify(token):
        return {
            "sub": "123456789",
            "email": "test@autopedicare.com",
            "email_verified": True,
        }

    # Path must be exactly where the ROUTE file imports it from
    monkeypatch.setattr("app.api.v1.auth.verify_google_token", mock_verify)

    # 2. Setup Transport
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # We send a dummy token; the mock will intercept it anyway
        payload = {"token": "valid_mock_token"}

        # 3. Call the endpoint
        response = await ac.post(
            "/api/v1/auth/google",
            json=payload,
            headers={"X-Forwarded-For": "1.1.1.1"},  # Speeds up middleware
        )

        # 4. Check results
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data


@pytest.mark.asyncio
async def test_middleware_rejection_logic():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        response = await ac.get("/debug-context")
        assert response.status_code == 200
        assert "captured_data" in response.json()


@pytest.mark.asyncio
async def test_apple_login_flow(monkeypatch):
    # Mock Apple verification
    async def mock_verify(token):
        return {
            "sub": "apple-123456",
            "email": "apple@example.com",
            "email_verified": True,
        }

    monkeypatch.setattr("app.api.v1.auth.verify_apple_token", mock_verify)

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
