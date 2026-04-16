from uuid import UUID
from fastapi import APIRouter, Depends, status, UploadFile, File, Form
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.user import User
from app.api.dependencies import get_current_user
from app.schemas.e_commerce.product_images import ProductImageResponse
from app.services.e_commerce.product_images import ProductImageService


router = APIRouter(tags=["Product Images"])


def get_image_service(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    return ProductImageService(db, current_user)


@router.post(
    "/products/{product_id}/images",
    response_model=ProductImageResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_product_image(
    product_id: UUID,
    file: UploadFile = File(...),
    angle_type: str = Form(default="front"),
    is_primary: bool = Form(default=False),
    service: ProductImageService = Depends(get_image_service),
):
    return await service.add_image(product_id, file, angle_type, is_primary)


@router.get("/products/{product_id}/images", response_model=list[ProductImageResponse])
async def get_product_images(product_id: UUID, db: Session = Depends(get_db)):
    service = ProductImageService(db)
    return service.get_product_images(product_id)


@router.delete("/images/{image_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product_image(
    image_id: UUID, service: ProductImageService = Depends(get_image_service)
):
    service.delete_image(image_id)
    return None
