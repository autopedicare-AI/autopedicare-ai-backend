from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.api.dependencies import get_current_user
from app.schemas.e_commerce.products import (
    ProductCreate,
    ProductResponse,
    ProductUpdate,
)
from app.services.e_commerce.products import ProductService


router = APIRouter(prefix="/products", tags=["Products"])


@router.post("/", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
def create_product(
    product_data: ProductCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    service = ProductService(db, current_user)
    return service.create_product(product_data)

@router.get("/me/{product_id}", response_model=ProductResponse)
def get_product_by_id(
    product_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get product details by ID. Authentication required."""
    service = ProductService(db, current_user)
    return service.get_product_by_id(product_id)


@router.put("/{product_id}", response_model=ProductResponse)
def update_product(
    product_id: str,
    product_data: ProductUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    service = ProductService(db, current_user)
    return service.update_product(product_id, product_data)


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product(
    product_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    service = ProductService(db, current_user)
    service.delete_product(product_id)


@router.get("/{product_id}", response_model=ProductResponse)
def list_public_product_by_id(
    product_id: str,
    db: Session = Depends(get_db),
):
    """Get product details by ID. No authentication required."""
    service = ProductService(db)
    return service.list_public_product_by_id(product_id)


@router.get("/", response_model=list[ProductResponse])
def list_products(
    skip: int = 0,
    limit: int = 10,
    db: Session = Depends(get_db),
):
    """List all active products. No authentication required."""
    service = ProductService(db)
    return service.list_all_active_products(skip, limit)


@router.get("/category/{category}", response_model=list[ProductResponse])
def list_products_by_category(
    category: str,
    skip: int = 0,
    limit: int = 10,
    db: Session = Depends(get_db),
):
    """List products by category. No authentication required."""
    service = ProductService(db)
    return service.list_products_by_category(category, skip, limit)
