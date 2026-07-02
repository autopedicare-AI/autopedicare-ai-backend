from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.db.session import get_db
from app.services.fleet.drivers import DriverService
from app.schemas.fleet.drivers import DriverCreate, DriverUpdate, DriverResponse

router = APIRouter(prefix="/drivers", tags=["Drivers"])


@router.post("", response_model=DriverResponse, status_code=201)
async def create_driver(driver: DriverCreate, db: AsyncSession = Depends(get_db)):
    service = DriverService(db)
    return await service.create_driver(driver)

@router.get("", response_model=List[DriverResponse])
async def get_drivers(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    service = DriverService(db)
    return await service.get_drivers(skip, limit)


@router.get("/{driver_id}", response_model=DriverResponse)
async def get_driver(driver_id: str, db: AsyncSession = Depends(get_db)):
    service = DriverService(db)
    return await service.get_driver(driver_id)


@router.put("/{driver_id}", response_model=DriverResponse)
async def update_driver(driver_id: str, driver: DriverUpdate, db: AsyncSession = Depends(get_db)):
    service = DriverService(db)
    return await service.update_driver(driver_id, driver)


@router.delete("/{driver_id}", status_code=204)
async def delete_driver(driver_id: str, db: AsyncSession = Depends(get_db)):
    service = DriverService(db)
    await service.delete_driver(driver_id)