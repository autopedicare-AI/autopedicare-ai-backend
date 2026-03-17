from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status
from typing import List
from uuid import UUID
from app.models.fleet.vehicles import Vehicle
from app.schemas.fleet.vehicles import VehicleCreate, VehicleUpdate, VehicleResponse


class VehicleService:
    def __init__(self, db: Session):
        self.db = db

    def create_vehicle(self, vehicle_data: VehicleCreate) -> VehicleResponse:
        vehicle = Vehicle(**vehicle_data.model_dump())
        self.db.add(vehicle)
        try:
            self.db.commit()
            self.db.refresh(vehicle)
            return VehicleResponse.model_validate(vehicle)
        except IntegrityError:
            self.db.rollback()
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Plate number already exists")

    def get_vehicle(self, vehicle_id: str) -> VehicleResponse:
        try:
            vehicle_uuid = UUID(vehicle_id)
        except ValueError:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid vehicle ID")
        vehicle = self.db.query(Vehicle).filter(Vehicle.id == vehicle_uuid).first()
        if not vehicle:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vehicle not found")
        return VehicleResponse.model_validate(vehicle)

    def get_vehicles(self, skip: int = 0, limit: int = 10) -> List[VehicleResponse]:
        vehicles = self.db.query(Vehicle).offset(skip).limit(limit).all()
        return [VehicleResponse.model_validate(v) for v in vehicles]

    def update_vehicle(self, vehicle_id: str, vehicle_data: VehicleUpdate) -> VehicleResponse:
        try:
            vehicle_uuid = UUID(vehicle_id)
        except ValueError:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid vehicle ID")
        vehicle = self.db.query(Vehicle).filter(Vehicle.id == vehicle_uuid).first()
        if not vehicle:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vehicle not found")
        for key, value in vehicle_data.model_dump(exclude_unset=True).items():
            setattr(vehicle, key, value)
        try:
            self.db.commit()
            self.db.refresh(vehicle)
            return VehicleResponse.model_validate(vehicle)
        except IntegrityError:
            self.db.rollback()
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Plate number already exists")

    def delete_vehicle(self, vehicle_id: str):
        try:
            vehicle_uuid = UUID(vehicle_id)
        except ValueError:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid vehicle ID")
        vehicle = self.db.query(Vehicle).filter(Vehicle.id == vehicle_uuid).first()
        if not vehicle:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vehicle not found")
        self.db.delete(vehicle)
        self.db.commit()