from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime
from uuid import UUID
from enum import Enum


class VehicleStatus(str, Enum):
    active = "active"
    maintenance = "maintenance"
    inactive = "inactive"


class VehicleBase(BaseModel):
    plate_number: str
    model: str
    manufacturer: str
    year: int
    vehicle_type: str
    status: VehicleStatus = VehicleStatus.active


class VehicleCreate(VehicleBase):
    pass


class VehicleUpdate(BaseModel):
    plate_number: Optional[str] = None
    model: Optional[str] = None
    manufacturer: Optional[str] = None
    year: Optional[int] = None
    vehicle_type: Optional[str] = None
    status: Optional[VehicleStatus] = None


class VehicleResponse(VehicleBase):
    id: UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)