from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status
from typing import List
from uuid import UUID
from app.models.fleet.vehicles import Vehicle
from app.schemas.fleet.vehicles import VehicleCreate, VehicleUpdate, VehicleResponse


class VehicleService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_vehicle(self, vehicle_data: VehicleCreate) -> VehicleResponse:
        vehicle = Vehicle(**vehicle_data.model_dump())
        self.db.add(vehicle)
        try:
            await self.db.commit()
            await self.db.refresh(vehicle)
            return VehicleResponse.model_validate(vehicle)
        except IntegrityError as e:
            await self.db.rollback()
            logger.error(
                "Vehicle create integrity error: {error}",
                error=e,
            )
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Plate number already exists",
            )
        except Exception:
            await self.db.rollback()
            logger.exception(
                "Vehicle create unexpected error}",
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error",
            )

    async def get_vehicle(self, vehicle_id: str) -> VehicleResponse:
        try:
            vehicle_uuid = UUID(vehicle_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid vehicle ID"
            )
        result = await self.db.execute(select(Vehicle).where(Vehicle.id == vehicle_uuid))
        vehicle = result.scalars().first()
        if not vehicle:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Vehicle not found"
            )
        return VehicleResponse.model_validate(vehicle)

    async def get_vehicles(self, skip: int = 0, limit: int = 10) -> List[VehicleResponse]:
        result = await self.db.execute(select(Vehicle).offset(skip).limit(limit))
        vehicles = result.scalars().all()
        return [VehicleResponse.model_validate(v) for v in vehicles]

    async def update_vehicle(
        self, vehicle_id: str, vehicle_data: VehicleUpdate
    ) -> VehicleResponse:
        try:
            vehicle_uuid = UUID(vehicle_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid vehicle ID"
            )
        result = await self.db.execute(select(Vehicle).where(Vehicle.id == vehicle_uuid))
        vehicle = result.scalars().first()
        if not vehicle:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Vehicle not found"
            )
        for key, value in vehicle_data.model_dump(exclude_unset=True).items():
            setattr(vehicle, key, value)
        try:
            await self.db.commit()
            await self.db.refresh(vehicle)
            return VehicleResponse.model_validate(vehicle)
        except IntegrityError as e:
            await self.db.rollback()
            logger.error(
                "Vehicle update integrity error: {error} | vehicle_id={vehicle_id}",
                error=e,
                vehicle_id=vehicle_id,
            )
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Plate number already exists",
            )
        except Exception:
            await self.db.rollback()
            logger.exception(
                "Vehicle update unexpected error: {error} | vehicle_id={vehicle_id}",
                vehicle_id=vehicle_id,
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error updating vehicle",
            )

    async def delete_vehicle(self, vehicle_id: str):
        try:
            vehicle_uuid = UUID(vehicle_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid vehicle ID"
            )
        result = await self.db.execute(select(Vehicle).where(Vehicle.id == vehicle_uuid))
        vehicle = result.scalars().first()
        if not vehicle:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Vehicle not found"
            )
        await self.db.delete(vehicle)
        await self.db.commit()
