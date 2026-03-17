from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime
from uuid import UUID
from enum import Enum


class TripStatus(str, Enum):
    ongoing = "ongoing"
    completed = "completed"
    cancelled = "cancelled"


class TripBase(BaseModel):
    driver_id: UUID
    vehicle_id: UUID
    start_location: str
    end_location: str
    start_time: datetime
    end_time: Optional[datetime] = None
    distance_km: float
    status: TripStatus = TripStatus.ongoing


class TripCreate(TripBase):
    pass


class TripUpdate(BaseModel):
    end_time: Optional[datetime] = None
    distance_km: Optional[float] = None
    status: Optional[TripStatus] = None


class TripResponse(TripBase):
    id: UUID

    model_config = ConfigDict(from_attributes=True)