from pydantic import BaseModel, ConfigDict
from uuid import UUID


class CartItemBase(BaseModel):
    product_id: UUID
    quantity: int


class CartItemCreate(CartItemBase):
    pass


class CartItemUpdate(BaseModel):
    quantity: int


class CartItemResponse(BaseModel):
    id: UUID
    product_id: UUID
    quantity: int
    product_name: str
    product_price: float
    subtotal: float

    model_config = ConfigDict(from_attributes=True)


class CartResponse(BaseModel):
    id: UUID
    user_id: UUID
    items: list[CartItemResponse]
    total_amount: float

    model_config = ConfigDict(from_attributes=True)
