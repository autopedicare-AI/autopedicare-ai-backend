from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import datetime


class ProductImageBase(BaseModel):
    product_id: UUID
    image_url: str
    angle_type: str
    display_order: int = 1
    is_primary: bool = False
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
    

class ProductImageCreate(ProductImageBase):
    pass


class ProductImageUpdate(BaseModel):
    image_url: str | None = None
    angle_type: str | None = None
    display_order: int | None = None
    is_primary: bool | None = None


class ProductImageResponse(ProductImageBase):
    id: UUID
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)