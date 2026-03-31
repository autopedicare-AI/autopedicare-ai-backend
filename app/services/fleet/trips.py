from loguru import logger
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from typing import List
from uuid import UUID
from app.models.fleet.trips import Trip
from app.schemas.fleet.trips import TripCreate, TripUpdate, TripResponse


class TripService:
    def __init__(self, db: Session):
        self.db = db

    def create_trip(self, trip_data: TripCreate) -> TripResponse:
        trip = Trip(**trip_data.model_dump())
        self.db.add(trip)
        try:
            self.db.commit()
            self.db.refresh(trip)
            return TripResponse.model_validate(trip)
        except Exception:
            self.db.rollback()
            logger.exception("Trip create error ")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error",
            )

    def get_trips(self, skip: int = 0, limit: int = 10) -> List[TripResponse]:
        trips = self.db.query(Trip).offset(skip).limit(limit).all()
        return [TripResponse.model_validate(t) for t in trips]

    def get_trip(self, trip_id: str) -> TripResponse:
        try:
            trip_uuid = UUID(trip_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid trip ID"
            )
        trip = self.db.query(Trip).filter(Trip.id == trip_uuid).first()
        if not trip:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Trip not found"
            )
        return TripResponse.model_validate(trip)

    def update_trip(self, trip_id: str, trip_data: TripUpdate) -> TripResponse:
        try:
            trip_uuid = UUID(trip_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid trip ID"
            )
        trip = self.db.query(Trip).filter(Trip.id == trip_uuid).first()
        if not trip:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Trip not found"
            )
        for key, value in trip_data.model_dump(exclude_unset=True).items():
            setattr(trip, key, value)
        try:
            self.db.commit()
            self.db.refresh(trip)
            return TripResponse.model_validate(trip)
        except Exception:
            self.db.rollback()
            logger.exception(
                "Trip update error | trip_id={trip_id}",
                trip_id=trip_id,
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error",
            )
