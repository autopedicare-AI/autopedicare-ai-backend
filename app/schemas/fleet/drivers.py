from pydantic import BaseModel, ConfigDict, EmailStr
from typing import Optional
from datetime import datetime
from uuid import UUID
from enum import Enum


class DriverStatus(str, Enum):
    active = "active"
    inactive = "inactive"


class DriverBase(BaseModel):
    full_name: str
    license_number: str
    phone_number: str
    email: EmailStr
    status: DriverStatus = DriverStatus.active


class DriverCreate(DriverBase):
    pass


class DriverUpdate(BaseModel):
    full_name: Optional[str] = None
    license_number: Optional[str] = None
    phone_number: Optional[str] = None
    email: Optional[EmailStr] = None
    status: Optional[DriverStatus] = None


class DriverResponse(DriverBase):
    id: UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)