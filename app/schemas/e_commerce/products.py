from pydantic import BaseModel, ConfigDict, Field, field_validator
from typing import Optional
from datetime import datetime
from uuid import UUID
from decimal import Decimal


class ProductPaginationParams(BaseModel):
    skip: int = Field(0, ge=0)
    limit: int = Field(10, ge=1)

    @field_validator("limit", mode="before")
    @classmethod
    def cap_limit(cls, value):
        try:
            value = int(value)
        except (TypeError, ValueError):
            raise ValueError("limit must be an integer")
        return min(max(value, 1), 100)

    @field_validator("skip", mode="before")
    @classmethod
    def normalize_skip(cls, value):
        try:
            value = int(value)
        except (TypeError, ValueError):
            raise ValueError("skip must be an integer")
        return max(value, 0)


class ProductBase(BaseModel):
    name: str
    description: Optional[str] = None
    category: str
    price: Decimal
    stock_quantity: int
    oem_number: Optional[str] = None
    brand: Optional[str] = None
    model: Optional[str] = None
    year_from: Optional[str] = None
    year_to: Optional[str] = None
    is_active: bool = True


class ProductCreate(ProductBase):
    pass


class ProductUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    price: Optional[Decimal] = None
    stock_quantity: Optional[int] = None
    oem_number: Optional[str] = None
    brand: Optional[str] = None
    model: Optional[str] = None
    year_from: Optional[str] = None
    year_to: Optional[str] = None
    is_active: Optional[bool] = None


class ProductResponse(ProductBase):
    id: UUID
    vendor_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
