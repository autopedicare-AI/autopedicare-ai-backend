from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.db.session import get_db
from app.services.fleet.trips import TripService
from app.schemas.fleet.trips import TripCreate, TripUpdate, TripResponse

router = APIRouter(prefix="/trips", tags=["Trips"])


@router.post("", response_model=TripResponse, status_code=201)
async def create_trip(trip: TripCreate, db: AsyncSession = Depends(get_db)):
    service = TripService(db)
    return await service.create_trip(trip)


@router.get("", response_model=List[TripResponse])
async def get_trips(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    service = TripService(db)
    return await service.get_trips(skip, limit)


@router.get("/{trip_id}", response_model=TripResponse)
async def get_trip(trip_id: str, db: AsyncSession = Depends(get_db)):
    service = TripService(db)
    return await service.get_trip(trip_id)


@router.put("/{trip_id}", response_model=TripResponse)
async def update_trip(trip_id: str, trip: TripUpdate, db: AsyncSession = Depends(get_db)):
    service = TripService(db)
    return await service.update_trip(trip_id, trip)