import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from datetime import datetime, timezone


@pytest.mark.asyncio
async def test_create_trip(auth_headers):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # Create driver
        driver_data = {
            "full_name": "Trip Driver",
            "license_number": "TRIP_DL",
            "phone_number": "+1234567890",
            "email": "trip.driver@example.com",
            "status": "active"
        }
        driver_response = await ac.post("/api/v1/drivers", json=driver_data, headers=auth_headers)
        assert driver_response.status_code == 201
        driver_id = driver_response.json()["id"]

        # Create vehicle
        vehicle_data = {
            "plate_number": "TRIP_PLATE",
            "model": "Trip Model",
            "manufacturer": "Trip Manufacturer",
            "year": 2023,
            "vehicle_type": "car",
            "status": "active"
        }
        vehicle_response = await ac.post("/api/v1/vehicles", json=vehicle_data, headers=auth_headers)
        assert vehicle_response.status_code == 201
        vehicle_id = vehicle_response.json()["id"]

        # Create trip
        trip_data = {
            "driver_id": driver_id,
            "vehicle_id": vehicle_id,
            "start_location": "New York",
            "end_location": "Boston",
            "start_time": datetime.now(timezone.utc).isoformat(),
            "distance_km": 350.5,
            "status": "ongoing"
        }
        response = await ac.post("/api/v1/trips", json=trip_data, headers=auth_headers)
        assert response.status_code == 201
        data = response.json()
        assert data["driver_id"] == driver_id
        assert data["vehicle_id"] == vehicle_id
        assert data["start_location"] == "New York"
        assert data["end_location"] == "Boston"
        assert data["distance_km"] == 350.5
        assert "id" in data


@pytest.mark.asyncio
async def test_get_trips(auth_headers):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/api/v1/trips", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


@pytest.mark.asyncio
async def test_update_trip(auth_headers):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # Create driver and vehicle
        driver_data = {
            "full_name": "Update Trip Driver",
            "license_number": "UPDATE_TRIP_DL",
            "phone_number": "+1234567890",
            "email": "update.trip.driver@example.com",
            "status": "active"
        }
        driver_response = await ac.post("/api/v1/drivers", json=driver_data, headers=auth_headers)
        driver_id = driver_response.json()["id"]

        vehicle_data = {
            "plate_number": "UPDATE_TRIP_PLATE",
            "model": "Update Trip Model",
            "manufacturer": "Update Trip Manufacturer",
            "year": 2023,
            "vehicle_type": "car",
            "status": "active"
        }
        vehicle_response = await ac.post("/api/v1/vehicles", json=vehicle_data, headers=auth_headers)
        vehicle_id = vehicle_response.json()["id"]

        # Create trip
        trip_data = {
            "driver_id": driver_id,
            "vehicle_id": vehicle_id,
            "start_location": "Los Angeles",
            "end_location": "San Francisco",
            "start_time": datetime.now(timezone.utc).isoformat(),
            "distance_km": 600.0,
            "status": "ongoing"
        }
        create_response = await ac.post("/api/v1/trips", json=trip_data, headers=auth_headers)
        trip_id = create_response.json()["id"]

        # Update trip
        update_data = {
            "status": "completed",
            "end_time": datetime.now(timezone.utc).isoformat(),
            "distance_km": 650.0
        }
        update_response = await ac.put(f"/api/v1/trips/{trip_id}", json=update_data, headers=auth_headers)
        assert update_response.status_code == 200
        data = update_response.json()
        assert data["status"] == "completed"
        assert data["distance_km"] == 650.0
        assert data["end_time"] is not None


@pytest.mark.asyncio
async def test_get_trip(auth_headers):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # Create driver and vehicle
        driver_data = {
            "full_name": "Get Trip Driver",
            "license_number": "GET_TRIP_DL",
            "phone_number": "+1234567890",
            "email": "get.trip.driver@example.com",
            "status": "active"
        }
        driver_response = await ac.post("/api/v1/drivers", json=driver_data, headers=auth_headers)
        driver_id = driver_response.json()["id"]

        vehicle_data = {
            "plate_number": "GET_TRIP_PLATE",
            "model": "Get Trip Model",
            "manufacturer": "Get Trip Manufacturer",
            "year": 2023,
            "vehicle_type": "car",
            "status": "active"
        }
        vehicle_response = await ac.post("/api/v1/vehicles", json=vehicle_data, headers=auth_headers)
        vehicle_id = vehicle_response.json()["id"]

        # Create trip
        trip_data = {
            "driver_id": driver_id,
            "vehicle_id": vehicle_id,
            "start_location": "Chicago",
            "end_location": "Detroit",
            "start_time": datetime.now(timezone.utc).isoformat(),
            "distance_km": 400.0,
            "status": "ongoing"
        }
        create_response = await ac.post("/api/v1/trips", json=trip_data, headers=auth_headers)
        trip_id = create_response.json()["id"]

        # Get specific trip
        get_response = await ac.get(f"/api/v1/trips/{trip_id}", headers=auth_headers)
        assert get_response.status_code == 200
        data = get_response.json()
        assert data["id"] == trip_id
        assert data["start_location"] == "Chicago"
        assert data["end_location"] == "Detroit"