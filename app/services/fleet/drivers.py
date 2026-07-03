from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status
from typing import List
from uuid import UUID
from app.models.fleet.drivers import Driver
from app.schemas.fleet.drivers import DriverCreate, DriverUpdate, DriverResponse


class DriverService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_driver(self, driver_data: DriverCreate) -> DriverResponse:
        driver = Driver(**driver_data.model_dump())
        self.db.add(driver)
        try:
            await self.db.commit()
            await self.db.refresh(driver)
            return DriverResponse.model_validate(driver)
        except IntegrityError:
            await self.db.rollback()
            logger.warning(
                "Driver create integrity error | email={}",
                driver_data.email,
            )
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A driver with this email or license number already exists",
            )
        except Exception:
            await self.db.rollback()
            logger.exception("Driver create unexpected error")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error",
            )

    async def get_driver(self, driver_id: str) -> DriverResponse:
        try:
            driver_uuid = UUID(driver_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid driver ID"
            )
        result = await self.db.execute(select(Driver).where(Driver.id == driver_uuid))
        driver = result.scalars().first()
        if not driver:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Driver not found"
            )
        return DriverResponse.model_validate(driver)

    async def get_drivers(self, skip: int = 0, limit: int = 10) -> List[DriverResponse]:
        result = await self.db.execute(
            select(Driver).offset(skip).limit(limit)
        )
        drivers = result.scalars().all()
        return [DriverResponse.model_validate(d) for d in drivers]

    async def update_driver(
        self, driver_id: str, driver_data: DriverUpdate
    ) -> DriverResponse:
        try:
            driver_uuid = UUID(driver_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid driver ID"
            )
        result = await self.db.execute(select(Driver).where(Driver.id == driver_uuid))
        driver = result.scalars().first()
        if not driver:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Driver not found"
            )
        for key, value in driver_data.model_dump(exclude_unset=True).items():
            setattr(driver, key, value)
        try:
            await self.db.commit()
            await self.db.refresh(driver)
            return DriverResponse.model_validate(driver)
        except IntegrityError:
            await self.db.rollback()
            logger.warning(
                "Driver update integrity error | driver_id={driver_id}",
                driver_id=driver_id,
            )
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="License number or email already exists",
            )
        except Exception:
            await self.db.rollback()
            logger.exception(
                "Driver update unexpected error| driver_id={driver_id}",
                driver_id=driver_id,
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error",
            )

    async def delete_driver(self, driver_id: str):
        try:
            driver_uuid = UUID(driver_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid driver ID"
            )
        result = await self.db.execute(select(Driver).where(Driver.id == driver_uuid))
        driver = result.scalars().first()
        if not driver:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Driver not found"
            )
        await self.db.delete(driver)
        await self.db.commit()
