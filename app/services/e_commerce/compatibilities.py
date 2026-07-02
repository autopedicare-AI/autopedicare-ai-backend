from uuid import UUID
from fastapi import HTTPException, status, UploadFile
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from loguru import logger

from app.models.e_commerce.compatibility import Compatibility
from app.models.user import User
from app.models.e_commerce.products import Product
from app.models.e_commerce.vendors import Vendor
from app.schemas.e_commerce.compatibility import (
    CompatibilityCreate,
    CompatibilityResponse,
    CompatibilityUpdate,
)
from app.schemas.e_commerce.products import ProductResponse


class CompatibilityService:

    def __init__(self, db: AsyncSession, current_user: User):
        self.db = db
        self.current_user = current_user
        self.vendor_id = None

    async def _get_user_vendor_id(self):
        if self.vendor_id is not None:
            return self.vendor_id
        result = await self.db.execute(
            select(Vendor).where(Vendor.owner_id == self.current_user.id)
        )
        vendor = result.scalars().first()
        if not vendor:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Vendor not found for the current user",
            )
        self.vendor_id = vendor.id
        return vendor.id

    async def create_compatibility(
        self, compatibility_data: CompatibilityCreate
    ) -> CompatibilityResponse:
        vendor_id = await self._get_user_vendor_id()
        result = await self.db.execute(
            select(Product)
            .options(
                selectinload(Product.vendor),
                selectinload(Product.images),
            )
            .where(
                Product.id == compatibility_data.product_id,
                Product.vendor_id == vendor_id,
            )
        )
        product = result.scalars().first()

        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found for the current user",
            )

        result = await self.db.execute(
            select(Compatibility).where(
                Compatibility.product_id == compatibility_data.product_id,
                Compatibility.vendor_id == vendor_id,
                Compatibility.car_brand == compatibility_data.car_brand,
                Compatibility.car_model == compatibility_data.car_model,
                Compatibility.year == compatibility_data.year,
                Compatibility.is_active == True,
            )
        )
        existing_compatibility = result.scalars().first()

        if existing_compatibility:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Compatibility already exists",
            )

        compatibility_dict = compatibility_data.model_dump()
        compatibility_dict["product_id"] = product.id
        compatibility_dict["vendor_id"] = vendor_id
        compatibility = Compatibility(**compatibility_dict)
        self.db.add(compatibility)
        try:
            await self.db.commit()
            await self.db.refresh(compatibility)
            return CompatibilityResponse.model_validate(compatibility)
        except SQLAlchemyError:
            await self.db.rollback()
            logger.exception(
                "Compatibility create error",
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error",
            )

    async def get_compatibility(self, compatibility_id: UUID) -> CompatibilityResponse:
        vendor_id = await self._get_user_vendor_id()
        result = await self.db.execute(
            select(Compatibility).where(
                Compatibility.id == compatibility_id,
                Compatibility.vendor_id == vendor_id,
            )
        )
        compatibility = result.scalars().first()

        if not compatibility:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Compatibility not found"
            )

        return CompatibilityResponse.model_validate(compatibility)

    async def update_compatibility(
        self, compatibility_id: UUID, compatibility_data: CompatibilityUpdate
    ) -> CompatibilityResponse:
        vendor_id = await self._get_user_vendor_id()
        result = await self.db.execute(
            select(Compatibility).where(
                Compatibility.id == compatibility_id,
                Compatibility.vendor_id == vendor_id,
            )
        )
        compatibility = result.scalars().first()

        if not compatibility:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Compatibility not found"
            )

        update_data = compatibility_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(compatibility, field, value)

        try:
            await self.db.commit()
            await self.db.refresh(compatibility)
            return CompatibilityResponse.model_validate(compatibility)
        except SQLAlchemyError:
            await self.db.rollback()
            logger.exception(
                "Compatibility update error",
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error",
            )

    async def delete_compatibility(self, compatibility_id: UUID):
        result = await self.db.execute(
            select(Compatibility)
            .join(Product)
            .join(Vendor)
            .where(
                Compatibility.id == compatibility_id,
                Vendor.owner_id == self.current_user.id,
            )
        )
        compatibility = result.scalars().first()

        if not compatibility:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Compatibility not found"
            )

        compatibility.is_active = False
        await self.db.commit()
        return {"detail": "Compatibility deleted successfully"}

    async def find_compatibilities_by_product_id(
        self, product_id: UUID, skip: int = 0, limit: int = 100
    ) -> list[CompatibilityResponse]:
        vendor_id = await self._get_user_vendor_id()
        result = await self.db.execute(
            select(Compatibility)
            .join(Product)
            .join(Vendor)
            .where(
                Compatibility.product_id == product_id,
                Compatibility.vendor_id == vendor_id,
            )
            .offset(skip)
            .limit(limit)
        )
        compatibilities = result.scalars().all()

        return [CompatibilityResponse.model_validate(c) for c in compatibilities]

    async def get_compatibilities_by_product(
        self, product_id: UUID, skip: int = 0, limit: int = 100
    ) -> list[CompatibilityResponse]:
        result = await self.db.execute(
            select(Compatibility)
            .where(
                Compatibility.product_id == product_id,
                Compatibility.is_active == True,
            )
            .offset(skip)
            .limit(limit)
        )
        compatibilities = result.scalars().all()

        return [CompatibilityResponse.model_validate(c) for c in compatibilities]

    async def smart_filter_search(
        self,
        car_brand: str,
        car_model: str,
        year: str,
        engine_type: str,
        skip: int = 0,
        limit: int = 100,
    ) -> list[ProductResponse]:
        result = await self.db.execute(
            select(Product)
            .options(
                selectinload(Product.vendor),
                selectinload(Product.images),
            )
            .join(Compatibility)
            .where(
                Product.is_active == True,
                Compatibility.is_active == True,
                Compatibility.car_brand.ilike(f"%{car_brand}%"),
                Compatibility.car_model.ilike(f"%{car_model}%"),
                Compatibility.year.ilike(f"%{year}%"),
                Compatibility.engine_type.ilike(f"%{engine_type}%"),
            )
            .offset(skip)
            .limit(limit)
        )
        products = result.scalars().all()
        return [ProductResponse.model_validate(p) for p in products]

    async def match_ai_identified_part(
        self, ai_label: str, car_brand: str, car_model: str, year: str
    ) -> dict:
        result = await self.db.execute(
            select(Product)
            .options(
                selectinload(Product.vendor),
                selectinload(Product.images),
            )
            .join(Compatibility)
            .where(
                Product.is_active == True,
                Compatibility.is_active == True,
                Compatibility.car_brand.ilike(f"%{car_brand}%"),
                Compatibility.car_model.ilike(f"%{car_model}%"),
                Compatibility.year.ilike(f"%{year}%"),
            )
        )
        matches = result.scalars().all()

        exact_matches = []
        alternatives = []
        exact_out_of_stock = False

        for p in matches:
            name = str(p.name).lower()
            category = str(p.category).lower()

            stock = int(getattr(p, "stock_quantity", 0))

            is_exact_match = (ai_label.lower() in name) or (
                ai_label.lower() in category
            )

            if is_exact_match:
                if stock > 0:
                    exact_matches.append(p)
                else:
                    exact_out_of_stock = True  # We found it, but it's empty!
            else:
                if stock > 0:
                    alternatives.append(p)

        if exact_matches:
            message = "Match found."
        elif exact_out_of_stock:
            if alternatives:
                message = f"Exact match for '{ai_label}' is out of stock. Showing alternatives."
            else:
                message = f"Exact match for '{ai_label}' is out of stock."
        elif alternatives:
            message = f"No exact match found for '{ai_label}'. Showing alternatives."
        else:
            message = "No compatible parts found."

        return {
            "identified_as": ai_label,
            "message": message,
            "exact_matches": [ProductResponse.model_validate(p) for p in exact_matches],
            "alternative_matches": [
                ProductResponse.model_validate(p) for p in alternatives
            ],
        }
