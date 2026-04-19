from uuid import UUID
from decimal import Decimal
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from sqlalchemy.exc import SQLAlchemyError
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
    def __init__(self, db: Session, current_user: User | None = None):
        self.db = db
        self.current_user = current_user

    def _get_vendor(self) -> Vendor:
        if not self.current_user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required",
            )

        vendor = (
            self.db.query(Vendor)
            .filter(Vendor.owner_id == self.current_user.id)
            .first()
        )
        if not vendor:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Vendor profile not found"
            )
        return vendor

    def create_product(self, product_data: ProductCreate) -> ProductResponse:
        vendor = self._get_vendor()

        product_dict = product_data.model_dump()
        product_dict["vendor_id"] = vendor.id

        product = Product(**product_dict)
        self.db.add(product)

        try:
            self.db.commit()
            self.db.refresh(product)
            return ProductResponse.model_validate(product)
        except SQLAlchemyError:
            self.db.rollback()
            logger.exception(
                "Product create error",
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error",
            )

    def get_product_by_id(self, product_id: UUID) -> ProductResponse:
        """Get a product by its ID, ensuring it belongs to the current user's vendor."""
        vendor = self._get_vendor()
        product = (
            self.db.query(Product)
            .filter(Product.id == product_id, Product.vendor_id == vendor.id)
            .first()
        )

        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found",
            )

        return ProductResponse.model_validate(product)

    def update_product(
        self, product_id: UUID, product_data: ProductUpdate
    ) -> ProductResponse:
        """Update a product by its ID, ensuring it belongs to the current user's vendor."""
        vendor = self._get_vendor()
        product = (
            self.db.query(Product)
            .filter(Product.id == product_id, Product.vendor_id == vendor.id)
            .first()
        )

        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found",
            )

        update_data = product_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(product, field, value)

        try:
            self.db.commit()
            self.db.refresh(product)
            return ProductResponse.model_validate(product)
        except SQLAlchemyError:
            self.db.rollback()
            logger.exception(
                "Product update error",
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error",
            )

    def delete_product(self, product_id: UUID):
        """Delete a product by its ID, ensuring it belongs to the current user's vendor."""
        vendor = self._get_vendor()  # Ensure vendor exists and belongs to current user
        product = (
            self.db.query(Product)
            .filter(Product.id == product_id, Product.vendor_id == vendor.id)
            .first()
        )

        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found",
            )

        product.is_active = False  # Soft delete by marking as inactive
        self.db.commit()
        return {"message": "Product deleted successfully"}

    def list_products_by_category(self, category: str, skip: int = 0, limit: int = 10):
        products = (
            self.db.query(Product)
            .filter(func.lower(Product.category) == category, Product.is_active == True)
            .offset(skip)
            .limit(limit)
            .all()
        )
        return [ProductResponse.model_validate(product) for product in products]

    def list_all_active_products(self, skip: int = 0, limit: int = 10):
        """Public: Browse all active products from all vendors."""
        products = (
            self.db.query(Product)
            .filter(Product.is_active == True)
            .offset(skip)
            .limit(limit)
            .all()
        )
        return [ProductResponse.model_validate(p) for p in products]

    def list_public_product_by_id(self, product_id: UUID) -> ProductResponse:
        """Public: View any active product details."""
        product = (
            self.db.query(Product)
            .filter(Product.id == product_id, Product.is_active == True)
            .first()
        )
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Product not found"
            )
        return ProductResponse.model_validate(product)
