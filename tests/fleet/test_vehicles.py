import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.api.dependencies import get_db
from sqlalchemy.orm import Session
from app.models.fleet.vehicles import Vehicle
from app.schemas.fleet.vehicles import VehicleCreate, VehicleStatus
import uuid


@pytest.fixture
def db_session():
    db = next(get_db())
    try:
        yield db
    finally:
        db.rollback()
        db.close()


@pytest.mark.asyncio
async def test_create_vehicle():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        vehicle_data = {
            "plate_number": "ABC123",
            "model": "Model X",
            "manufacturer": "Tesla",
            "year": 2023,
            "vehicle_type": "car",
            "status": "active"
        }

        response = await ac.post("/api/v1/vehicles", json=vehicle_data)
        assert response.status_code == 201
        data = response.json()
        assert data["plate_number"] == "ABC123"
        assert data["model"] == "Model X"
        assert "id" in data
        assert "created_at" in data


@pytest.mark.asyncio
async def test_get_vehicles():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/api/v1/vehicles")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


@pytest.mark.asyncio
async def test_create_duplicate_vehicle():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        vehicle_data = {
            "plate_number": "DUPLICATE123",
            "model": "Model Y",
            "manufacturer": "Tesla",
            "year": 2023,
            "vehicle_type": "car",
            "status": "active"
        }

        # Create first
        response1 = await ac.post("/api/v1/vehicles", json=vehicle_data)
        assert response1.status_code == 201

        # Try to create duplicate
        response2 = await ac.post("/api/v1/vehicles", json=vehicle_data)
        assert response2.status_code == 400
        assert "Plate number already exists" in response2.json()["detail"]


@pytest.mark.asyncio
async def test_update_vehicle():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # Create vehicle
        vehicle_data = {
            "plate_number": "UPDATE123",
            "model": "Model S",
            "manufacturer": "Tesla",
            "year": 2022,
            "vehicle_type": "car",
            "status": "active"
        }
        create_response = await ac.post("/api/v1/vehicles", json=vehicle_data)
        assert create_response.status_code == 201
        vehicle_id = create_response.json()["id"]

        # Update vehicle
        update_data = {"status": "maintenance"}
        update_response = await ac.put(f"/api/v1/vehicles/{vehicle_id}", json=update_data)
        assert update_response.status_code == 200
        data = update_response.json()
        assert data["status"] == "maintenance"


@pytest.mark.asyncio
async def test_delete_vehicle():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # Create vehicle
        vehicle_data = {
            "plate_number": "DELETE123",
            "model": "Model 3",
            "manufacturer": "Tesla",
            "year": 2021,
            "vehicle_type": "car",
            "status": "active"
        }
        create_response = await ac.post("/api/v1/vehicles", json=vehicle_data)
        assert create_response.status_code == 201
        vehicle_id = create_response.json()["id"]

        # Delete vehicle
        delete_response = await ac.delete(f"/api/v1/vehicles/{vehicle_id}")
        assert delete_response.status_code == 204

        # Try to get deleted vehicle
        get_response = await ac.get(f"/api/v1/vehicles/{vehicle_id}")
        assert get_response.status_code == 404