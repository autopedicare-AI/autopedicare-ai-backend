from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime
from uuid import UUID
from decimal import Decimal


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
