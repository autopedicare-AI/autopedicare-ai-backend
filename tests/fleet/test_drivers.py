import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.mark.asyncio
async def test_create_driver(auth_headers):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        driver_data = {
            "full_name": "John Doe",
            "license_number": "DL123456",
            "phone_number": "+1234567890",
            "email": "john.doe@example.com",
            "status": "active"
        }

        response = await ac.post("/api/v1/drivers", json=driver_data, headers=auth_headers)
        assert response.status_code == 201
        data = response.json()
        assert data["full_name"] == "John Doe"
        assert data["license_number"] == "DL123456"
        assert data["email"] == "john.doe@example.com"
        assert "id" in data
        assert "created_at" in data


@pytest.mark.asyncio
async def test_get_drivers(auth_headers):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/api/v1/drivers", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


@pytest.mark.asyncio
async def test_create_duplicate_driver(auth_headers):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        driver_data = {
            "full_name": "Jane Smith",
            "license_number": "DUPLICATE_DL",
            "phone_number": "+0987654321",
            "email": "jane.smith@example.com",
            "status": "active"
        }

        # Create first
        response1 = await ac.post("/api/v1/drivers", json=driver_data, headers=auth_headers)
        assert response1.status_code == 201

        # Try to create duplicate license
        driver_data_dup = driver_data.copy()
        driver_data_dup["email"] = "different@example.com"
        response2 = await ac.post("/api/v1/drivers", json=driver_data_dup, headers=auth_headers)
        assert response2.status_code == 409

        # Try to create duplicate email
        driver_data_dup2 = driver_data.copy()
        driver_data_dup2["license_number"] = "DIFFERENT_DL"
        response3 = await ac.post("/api/v1/drivers", json=driver_data_dup2, headers=auth_headers)
        assert response3.status_code == 409


@pytest.mark.asyncio
async def test_update_driver(auth_headers):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # Create driver
        driver_data = {
            "full_name": "Bob Wilson",
            "license_number": "UPDATE_DL",
            "phone_number": "+1122334455",
            "email": "bob.wilson@example.com",
            "status": "active"
        }
        create_response = await ac.post("/api/v1/drivers", json=driver_data, headers=auth_headers)
        assert create_response.status_code == 201
        driver_id = create_response.json()["id"]

        # Update driver
        update_data = {"status": "inactive"}
        update_response = await ac.put(f"/api/v1/drivers/{driver_id}", json=update_data, headers=auth_headers)
        assert update_response.status_code == 200
        data = update_response.json()
        assert data["status"] == "inactive"


@pytest.mark.asyncio
async def test_delete_driver(auth_headers):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # Create driver
        driver_data = {
            "full_name": "Alice Brown",
            "license_number": "DELETE_DL",
            "phone_number": "+5566778899",
            "email": "alice.brown@example.com",
            "status": "active"
        }
        create_response = await ac.post("/api/v1/drivers", json=driver_data, headers=auth_headers)
        assert create_response.status_code == 201
        driver_id = create_response.json()["id"]

        # Delete driver
        delete_response = await ac.delete(f"/api/v1/drivers/{driver_id}", headers=auth_headers)
        assert delete_response.status_code == 204

        # Try to get deleted driver
        get_response = await ac.get(f"/api/v1/drivers/{driver_id}", headers=auth_headers)
        assert get_response.status_code == 404