import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
import uuid


@pytest.mark.asyncio
async def test_create_assignment(auth_headers):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # Create driver
        driver_data = {
            "full_name": "Test Driver",
            "license_number": "ASSIGN_DL",
            "phone_number": "+1234567890",
            "email": "test.driver@example.com",
            "status": "active"
        }
        driver_response = await ac.post("/api/v1/drivers", json=driver_data, headers=auth_headers)
        assert driver_response.status_code == 201
        driver_id = driver_response.json()["id"]

        # Create vehicle
        vehicle_data = {
            "plate_number": "ASSIGN_PLATE",
            "model": "Test Model",
            "manufacturer": "Test Manufacturer",
            "year": 2023,
            "vehicle_type": "car",
            "status": "active"
        }
        vehicle_response = await ac.post("/api/v1/vehicles", json=vehicle_data, headers=auth_headers)
        assert vehicle_response.status_code == 201
        vehicle_id = vehicle_response.json()["id"]

        # Create assignment
        assignment_data = {
            "driver_id": driver_id,
            "vehicle_id": vehicle_id,
            "status": "active"
        }
        response = await ac.post("/api/v1/assignments", json=assignment_data, headers=auth_headers)
        assert response.status_code == 201
        data = response.json()
        assert data["driver_id"] == driver_id
        assert data["vehicle_id"] == vehicle_id
        assert data["status"] == "active"
        assert "id" in data
        assert "assigned_at" in data


@pytest.mark.asyncio
async def test_get_assignments(auth_headers):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/api/v1/assignments", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


@pytest.mark.asyncio
async def test_duplicate_assignment(auth_headers):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # Create driver
        driver_data = {
            "full_name": "Dup Driver",
            "license_number": "DUP_DL",
            "phone_number": "+1234567890",
            "email": "dup.driver@example.com",
            "status": "active"
        }
        driver_response = await ac.post("/api/v1/drivers", json=driver_data, headers=auth_headers)
        assert driver_response.status_code == 201
        driver_id = driver_response.json()["id"]

        # Create vehicle
        vehicle_data = {
            "plate_number": "DUP_PLATE",
            "model": "Dup Model",
            "manufacturer": "Dup Manufacturer",
            "year": 2023,
            "vehicle_type": "car",
            "status": "active"
        }
        vehicle_response = await ac.post("/api/v1/vehicles", json=vehicle_data, headers=auth_headers)
        assert vehicle_response.status_code == 201
        vehicle_id = vehicle_response.json()["id"]

        # Create first assignment
        assignment_data = {
            "driver_id": driver_id,
            "vehicle_id": vehicle_id,
            "status": "active"
        }
        response1 = await ac.post("/api/v1/assignments", json=assignment_data, headers=auth_headers)
        assert response1.status_code == 201

        # Try to create duplicate assignment for same driver
        response2 = await ac.post("/api/v1/assignments", json=assignment_data, headers=auth_headers)
        assert response2.status_code == 409
        assert "Driver already assigned" in response2.json()["detail"]


@pytest.mark.asyncio
async def test_update_assignment(auth_headers):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # Create driver and vehicle
        driver_data = {
            "full_name": "Update Driver",
            "license_number": "UPDATE_ASSIGN_DL",
            "phone_number": "+1234567890",
            "email": "update.driver@example.com",
            "status": "active"
        }
        driver_response = await ac.post("/api/v1/drivers", json=driver_data, headers=auth_headers)
        driver_id = driver_response.json()["id"]

        vehicle_data = {
            "plate_number": "UPDATE_ASSIGN_PLATE",
            "model": "Update Model",
            "manufacturer": "Update Manufacturer",
            "year": 2023,
            "vehicle_type": "car",
            "status": "active"
        }
        vehicle_response = await ac.post("/api/v1/vehicles", json=vehicle_data, headers=auth_headers)
        vehicle_id = vehicle_response.json()["id"]

        # Create assignment
        assignment_data = {
            "driver_id": driver_id,
            "vehicle_id": vehicle_id,
            "status": "active"
        }
        create_response = await ac.post("/api/v1/assignments", json=assignment_data, headers=auth_headers)
        assignment_id = create_response.json()["id"]

        # Update assignment
        update_data = {"status": "inactive"}
        update_response = await ac.put(f"/api/v1/assignments/{assignment_id}", json=update_data, headers=auth_headers)
        assert update_response.status_code == 200
        data = update_response.json()
        assert data["status"] == "inactive"


@pytest.mark.asyncio
async def test_delete_assignment(auth_headers):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # Create driver and vehicle
        driver_data = {
            "full_name": "Delete Driver",
            "license_number": "DELETE_ASSIGN_DL",
            "phone_number": "+1234567890",
            "email": "delete.driver@example.com",
            "status": "active"
        }
        driver_response = await ac.post("/api/v1/drivers", json=driver_data, headers=auth_headers)
        driver_id = driver_response.json()["id"]

        vehicle_data = {
            "plate_number": "DELETE_ASSIGN_PLATE",
            "model": "Delete Model",
            "manufacturer": "Delete Manufacturer",
            "year": 2023,
            "vehicle_type": "car",
            "status": "active"
        }
        vehicle_response = await ac.post("/api/v1/vehicles", json=vehicle_data, headers=auth_headers)
        vehicle_id = vehicle_response.json()["id"]

        # Create assignment
        assignment_data = {
            "driver_id": driver_id,
            "vehicle_id": vehicle_id,
            "status": "active"
        }
        create_response = await ac.post("/api/v1/assignments", json=assignment_data, headers=auth_headers)
        assignment_id = create_response.json()["id"]

        # Delete assignment
        delete_response = await ac.delete(f"/api/v1/assignments/{assignment_id}", headers=auth_headers)
        assert delete_response.status_code == 204