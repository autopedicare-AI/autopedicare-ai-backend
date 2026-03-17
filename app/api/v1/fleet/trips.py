from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List
from app.api.dependencies import get_db
from app.services.fleet.trips import TripService
from app.schemas.fleet.trips import TripCreate, TripUpdate, TripResponse

router = APIRouter(prefix="/trips", tags=["Trips"])


@router.post("", response_model=TripResponse, status_code=201)
def create_trip(trip: TripCreate, db: Session = Depends(get_db)):
    service = TripService(db)
    return service.create_trip(trip)


@router.get("", response_model=List[TripResponse])
def get_trips(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db)
):
    service = TripService(db)
    return service.get_trips(skip, limit)


@router.get("/{trip_id}", response_model=TripResponse)
def get_trip(trip_id: str, db: Session = Depends(get_db)):
    service = TripService(db)
    return service.get_trip(trip_id)


@router.put("/{trip_id}", response_model=TripResponse)
def update_trip(trip_id: str, trip: TripUpdate, db: Session = Depends(get_db)):
    service = TripService(db)
    return service.update_trip(trip_id, trip)