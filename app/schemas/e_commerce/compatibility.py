from pydantic import BaseModel, ConfigDict
from typing import Optional
from uuid import UUID
from datetime import datetime


class CompatibilityBase(BaseModel):
    product_id: UUID
    car_brand: str
    car_model: str
    year: Optional[str] = None
    engine_type: Optional[str] = None
    is_active: Optional[bool] = True


class CompatibilityCreate(CompatibilityBase):
    pass


class CompatibilityUpdate(BaseModel):
    car_brand: Optional[str] = None
    car_model: Optional[str] = None
    year: Optional[str] = None
    engine_type: Optional[str] = None
    is_active: Optional[bool] = None


class CompatibilityResponse(CompatibilityBase):
    id: UUID
    vendor_id: UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
