from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.db.session import get_db
from app.services.fleet.vehicles import VehicleService
from app.schemas.fleet.vehicles import VehicleCreate, VehicleUpdate, VehicleResponse

router = APIRouter(prefix="/vehicles", tags=["Vehicles"])


@router.post("", response_model=VehicleResponse, status_code=201)
async def create_vehicle(vehicle: VehicleCreate, db: AsyncSession = Depends(get_db)):
    service = VehicleService(db)
    return await service.create_vehicle(vehicle)


@router.get("", response_model=List[VehicleResponse])
async def get_vehicles(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    service = VehicleService(db)
    return await service.get_vehicles(skip, limit)


@router.get("/{vehicle_id}", response_model=VehicleResponse)
async def get_vehicle(vehicle_id: str, db: AsyncSession = Depends(get_db)):
    service = VehicleService(db)
    return await service.get_vehicle(vehicle_id)


@router.put("/{vehicle_id}", response_model=VehicleResponse)
async def update_vehicle(vehicle_id: str, vehicle: VehicleUpdate, db: AsyncSession = Depends(get_db)):
    service = VehicleService(db)
    return await service.update_vehicle(vehicle_id, vehicle)


@router.delete("/{vehicle_id}", status_code=204)
async def delete_vehicle(vehicle_id: str, db: AsyncSession = Depends(get_db)):
    service = VehicleService(db)
    await service.delete_vehicle(vehicle_id)