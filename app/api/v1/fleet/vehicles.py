from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List
from app.db.session import get_db
from app.services.fleet.vehicles import VehicleService
from app.schemas.fleet.vehicles import VehicleCreate, VehicleUpdate, VehicleResponse

router = APIRouter(prefix="/vehicles", tags=["Vehicles"])


@router.post("", response_model=VehicleResponse, status_code=201)
def create_vehicle(vehicle: VehicleCreate, db: Session = Depends(get_db)):
    service = VehicleService(db)
    return service.create_vehicle(vehicle)


@router.get("", response_model=List[VehicleResponse])
def get_vehicles(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db)
):
    service = VehicleService(db)
    return service.get_vehicles(skip, limit)


@router.get("/{vehicle_id}", response_model=VehicleResponse)
def get_vehicle(vehicle_id: str, db: Session = Depends(get_db)):
    service = VehicleService(db)
    return service.get_vehicle(vehicle_id)


@router.put("/{vehicle_id}", response_model=VehicleResponse)
def update_vehicle(vehicle_id: str, vehicle: VehicleUpdate, db: Session = Depends(get_db)):
    service = VehicleService(db)
    return service.update_vehicle(vehicle_id, vehicle)


@router.delete("/{vehicle_id}", status_code=204)
def delete_vehicle(vehicle_id: str, db: Session = Depends(get_db)):
    service = VehicleService(db)
    service.delete_vehicle(vehicle_id)