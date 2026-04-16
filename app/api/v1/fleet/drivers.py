from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List
from app.db.session import get_db
from app.services.fleet.drivers import DriverService
from app.schemas.fleet.drivers import DriverCreate, DriverUpdate, DriverResponse

router = APIRouter(prefix="/drivers", tags=["Drivers"])


@router.post("", response_model=DriverResponse, status_code=201)
def create_driver(driver: DriverCreate, db: Session = Depends(get_db)):
    service = DriverService(db)
    return service.create_driver(driver)


@router.get("", response_model=List[DriverResponse])
def get_drivers(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db)
):
    service = DriverService(db)
    return service.get_drivers(skip, limit)


@router.get("/{driver_id}", response_model=DriverResponse)
def get_driver(driver_id: str, db: Session = Depends(get_db)):
    service = DriverService(db)
    return service.get_driver(driver_id)


@router.put("/{driver_id}", response_model=DriverResponse)
def update_driver(driver_id: str, driver: DriverUpdate, db: Session = Depends(get_db)):
    service = DriverService(db)
    return service.update_driver(driver_id, driver)


@router.delete("/{driver_id}", status_code=204)
def delete_driver(driver_id: str, db: Session = Depends(get_db)):
    service = DriverService(db)
    service.delete_driver(driver_id)