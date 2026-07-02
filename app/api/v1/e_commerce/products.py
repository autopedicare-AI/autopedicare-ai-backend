from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.db.session import get_db
from app.api.dependencies import get_current_user
from app.schemas.e_commerce.products import (
    ProductCreate,
    ProductPaginationParams,
    ProductResponse,
    ProductUpdate,
)
from app.services.e_commerce.products import ProductService

router = APIRouter(prefix="/products", tags=["Products"])


@router.post("/", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
async def create_product(
    product_data: ProductCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    service = ProductService(db, current_user)
    return await service.create_product(product_data)


@router.get("/me/{product_id}", response_model=ProductResponse)
async def get_product_by_id(
    product_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get product details by ID. Authentication required."""
    service = ProductService(db, current_user)
    return await service.get_product_by_id(product_id)


@router.put("/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: UUID,
    product_data: ProductUpdate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    service = ProductService(db, current_user)
    return await service.update_product(product_id, product_data)


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(
    product_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    service = ProductService(db, current_user)
    await service.delete_product(product_id)
    return None


@router.get("/{product_id}", response_model=ProductResponse)
async def list_public_product_by_id(
    product_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get product details by ID. No authentication required."""
    service = ProductService(db)
    return await service.list_public_product_by_id(product_id)


@router.get("/", response_model=list[ProductResponse])
async def list_products(
    pagination: ProductPaginationParams = Depends(),
    db: AsyncSession = Depends(get_db),
):
    """List all active products. No authentication required."""
    service = ProductService(db)
    return await service.list_all_active_products(pagination.skip, pagination.limit)


@router.get("/category/{category}", response_model=list[ProductResponse])
async def list_products_by_category(
    category: str,
    pagination: ProductPaginationParams = Depends(),
    db: AsyncSession = Depends(get_db),
):
    """List products by category. No authentication required."""
    service = ProductService(db)
    return await service.list_products_by_category(category, pagination.skip, pagination.limit)
