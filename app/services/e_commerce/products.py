from uuid import UUID
from fastapi import HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import selectinload
from loguru import logger

from app.models.e_commerce.products import Product
from app.models.user import User
from app.models.e_commerce.vendors import Vendor
from app.schemas.e_commerce.products import (
    ProductCreate,
    ProductResponse,
    ProductUpdate,
)


class ProductService:
    def __init__(self, db: AsyncSession, current_user: User | None = None):
        self.db = db
        self.current_user = current_user

    async def _get_vendor(self) -> Vendor:
        if not self.current_user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required",
            )

        result = await self.db.execute(
            select(Vendor).where(Vendor.owner_id == self.current_user.id)
        )
        vendor = result.scalars().first()
        if not vendor:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Vendor profile not found"
            )
        return vendor

    async def _get_vendor_product(
        self, product_id: UUID, for_update: bool = False
    ) -> Product:

        vendor = await self._get_vendor()
        vendor_id = vendor.id

        query = (
            select(Product)
            .options(
                selectinload(Product.vendor),
                selectinload(Product.images),
            )
            .where(Product.id == product_id, Product.vendor_id == vendor_id)
        )

        if for_update:
            query = query.with_for_update()

        result = await self.db.execute(query)
        product = result.scalars().first()
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Product not found"
            )
        return product

    async def create_product(self, product_data: ProductCreate) -> ProductResponse:
        vendor = await self._get_vendor()

        product_dict = product_data.model_dump()
        product_dict["vendor_id"] = vendor.id

        product = Product(**product_dict)
        self.db.add(product)

        try:
            await self.db.commit()
            await self.db.refresh(product)
            return ProductResponse.model_validate(product)
        except SQLAlchemyError:
            await self.db.rollback()
            logger.exception(
                "Product create error",
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error",
            )

    async def get_product_by_id(self, product_id: UUID) -> ProductResponse:
        product = await self._get_vendor_product(product_id)

        return ProductResponse.model_validate(product)

    async def update_product(
        self, product_id: UUID, product_data: ProductUpdate
    ) -> ProductResponse:
        product = await self._get_vendor_product(product_id, for_update=True)

        update_data = product_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(product, field, value)

        try:
            await self.db.commit()
            await self.db.refresh(product)
            return ProductResponse.model_validate(product)
        except SQLAlchemyError:
            await self.db.rollback()
            logger.exception(
                "Product update error",
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error",
            )

    async def delete_product(self, product_id: UUID):
        product = await self._get_vendor_product(product_id, for_update=True)

        product.is_active = False
        try:
            await self.db.commit()
        except SQLAlchemyError:
            await self.db.rollback()
            logger.exception(
                "Product delete error",
            )
        return {"message": "Product deleted successfully"}

    async def list_products_by_category(
        self, category: str, skip: int = 0, limit: int = 10
    ):
        result = await self.db.execute(
            select(Product)
            .options(
                selectinload(Product.vendor),
                selectinload(Product.images),
            )
            .where(
                func.lower(Product.category) == category.lower(),
                Product.is_active.is_(True),
            )
            .offset(skip)
            .limit(limit)
            .order_by(Product.created_at.desc())
        )
        products = result.scalars().all()
        return [ProductResponse.model_validate(product) for product in products]

    async def list_all_active_products(self, skip: int = 0, limit: int = 10):
        result = await self.db.execute(
            select(Product)
            .options(
                selectinload(Product.vendor),
                selectinload(Product.images),
            )
            .where(Product.is_active.is_(True))
            .offset(skip)
            .limit(limit)
            .order_by(Product.created_at.desc())
        )
        products = result.scalars().all()
        return [ProductResponse.model_validate(p) for p in products]

    async def list_public_product_by_id(self, product_id: UUID) -> ProductResponse:
        result = await self.db.execute(
            select(Product)
            .options(
                selectinload(Product.vendor),
                selectinload(Product.images),
            )
            .where(Product.id == product_id, Product.is_active.is_(True))
        )
        product = result.scalars().first()
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Product not found"
            )
        return ProductResponse.model_validate(product)
