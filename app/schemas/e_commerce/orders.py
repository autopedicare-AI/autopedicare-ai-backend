from pydantic import BaseModel, ConfigDict
from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID
from decimal import Decimal


class Status(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


class OrderItemResponse(BaseModel):
    id: UUID
    product_id: Optional[UUID]
    quantity: int
    unit_price: Decimal
    sub_total: Decimal

    model_config = ConfigDict(from_attributes=True)


class OrderCreate(BaseModel):
    shipping_address: str


class OrderUpdate(BaseModel):
    status: Optional[Status] = None
    payment_status: Optional[str] = None
    payment_reference: Optional[str] = None
    shipping_address: Optional[str] = None


class OrderResponse(BaseModel):
    id: UUID
    user_id: UUID
    total_amount: Decimal
    status: Status
    payment_status: str
    payment_reference: Optional[str]
    shipping_address: str
    authorization_url: Optional[str]
    items: list[OrderItemResponse]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
