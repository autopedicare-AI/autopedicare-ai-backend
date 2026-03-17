from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status
from typing import List
from uuid import UUID
from app.models.fleet.drivers import Driver
from app.schemas.fleet.drivers import DriverCreate, DriverUpdate, DriverResponse


class DriverService:
    def __init__(self, db: Session):
        self.db = db

    def create_driver(self, driver_data: DriverCreate) -> DriverResponse:
        driver = Driver(**driver_data.model_dump())
        self.db.add(driver)
        try:
            self.db.commit()
            self.db.refresh(driver)
            return DriverResponse.model_validate(driver)
        except IntegrityError:
            self.db.rollback()
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="License number or email already exists")

    def get_driver(self, driver_id: str) -> DriverResponse:
        try:
            driver_uuid = UUID(driver_id)
        except ValueError:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid driver ID")
        driver = self.db.query(Driver).filter(Driver.id == driver_uuid).first()
        if not driver:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Driver not found")
        return DriverResponse.model_validate(driver)

    def get_drivers(self, skip: int = 0, limit: int = 10) -> List[DriverResponse]:
        drivers = self.db.query(Driver).offset(skip).limit(limit).all()
        return [DriverResponse.model_validate(d) for d in drivers]

    def update_driver(self, driver_id: str, driver_data: DriverUpdate) -> DriverResponse:
        try:
            driver_uuid = UUID(driver_id)
        except ValueError:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid driver ID")
        driver = self.db.query(Driver).filter(Driver.id == driver_uuid).first()
        if not driver:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Driver not found")
        for key, value in driver_data.model_dump(exclude_unset=True).items():
            setattr(driver, key, value)
        try:
            self.db.commit()
            self.db.refresh(driver)
            return DriverResponse.model_validate(driver)
        except IntegrityError:
            self.db.rollback()
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="License number or email already exists")

    def delete_driver(self, driver_id: str):
        try:
            driver_uuid = UUID(driver_id)
        except ValueError:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid driver ID")
        driver = self.db.query(Driver).filter(Driver.id == driver_uuid).first()
        if not driver:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Driver not found")
        self.db.delete(driver)
        self.db.commit()