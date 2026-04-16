from uuid import UUID
from fastapi import HTTPException, status, UploadFile
from sqlalchemy.orm import Session
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

    def __init__(self, db: Session, current_user: User):
        self.db = db
        self.current_user = current_user
        self.vendor_id = self._get_user_vendor_id()

    def _get_user_vendor_id(self):
        vendor = (
            self.db.query(Vendor)
            .filter(Vendor.owner_id == self.current_user.id)
            .first()
        )
        if not vendor:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Vendor not found for the current user",
            )
        return vendor.id

    def create_compatibility(
        self, compatibility_data: CompatibilityCreate
    ) -> CompatibilityResponse:
        product = (
            self.db.query(Product)
            .filter(
                Product.id == compatibility_data.product_id,
                Product.vendor_id == self.vendor_id,
            )
            .first()
        )

        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found for the current user",
            )

        existing_compatibility = (
            self.db.query(Compatibility)
            .filter(
                Compatibility.product_id == compatibility_data.product_id,
                Compatibility.vendor_id == self.vendor_id,
                Compatibility.car_brand == compatibility_data.car_brand,
                Compatibility.car_model == compatibility_data.car_model,
                Compatibility.year == compatibility_data.year,
                Compatibility.is_active == True,
            )
            .first()
        )

        if existing_compatibility:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Compatibility already exists",
            )

        compatibility_dict = compatibility_data.model_dump()
        compatibility_dict["product_id"] = product.id
        compatibility_dict["vendor_id"] = self.vendor_id
        compatibility = Compatibility(**compatibility_dict)
        self.db.add(compatibility)
        try:
            self.db.commit()
            self.db.refresh(compatibility)
            return CompatibilityResponse.model_validate(compatibility)
        except SQLAlchemyError:
            self.db.rollback()
            logger.exception(
                "Compatibility create error",
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error",
            )

    def get_compatibility(self, compatibility_id: UUID) -> CompatibilityResponse:
        compatibility = (
            self.db.query(Compatibility)
            .filter(
                Compatibility.id == compatibility_id,
                Compatibility.vendor_id == self.vendor_id,
            )
            .first()
        )

        if not compatibility:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Compatibility not found"
            )

        return CompatibilityResponse.model_validate(compatibility)

    def update_compatibility(
        self, compatibility_id: UUID, compatibility_data: CompatibilityUpdate
    ) -> CompatibilityResponse:
        compatibility = (
            self.db.query(Compatibility)
            .filter(
                Compatibility.id == compatibility_id,
                Compatibility.vendor_id == self.vendor_id,
            )
            .first()
        )

        if not compatibility:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Compatibility not found"
            )

        update_data = compatibility_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(compatibility, field, value)

        try:
            self.db.commit()
            self.db.refresh(compatibility)
            return CompatibilityResponse.model_validate(compatibility)
        except SQLAlchemyError:
            self.db.rollback()
            logger.exception(
                "Compatibility update error",
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error",
            )

    def delete_compatibility(self, compatibility_id: UUID):
        compatibility = (
            self.db.query(Compatibility)
            .join(Product)
            .join(Vendor)
            .filter(
                Compatibility.id == compatibility_id,
                Vendor.owner_id == self.current_user.id,
            )
            .first()
        )

        if not compatibility:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Compatibility not found"
            )

        compatibility.is_active = False
        self.db.commit()
        return {"detail": "Compatibility deleted successfully"}

    def find_compatibilities_by_product_id(
        self, product_id: UUID, skip: int = 0, limit: int = 100
    ) -> list[CompatibilityResponse]:
        compatibilities = (
            self.db.query(Compatibility)
            .join(Product)
            .join(Vendor)
            .filter(
                Compatibility.product_id == product_id,
                Compatibility.vendor_id == self.vendor_id,
            )
            .offset(skip)
            .limit(limit)
            .all()
        )

        return [CompatibilityResponse.model_validate(c) for c in compatibilities]

    def get_compatibilities_by_product(
        self, product_id: UUID, skip: int = 0, limit: int = 100
    ) -> list[CompatibilityResponse]:
        compatibilities = (
            self.db.query(Compatibility)
            .filter(
                Compatibility.product_id == product_id,
                Compatibility.is_active == True,
            )
            .offset(skip)
            .limit(limit)
            .all()
        )

        return [CompatibilityResponse.model_validate(c) for c in compatibilities]

    def smart_filter_search(
        self,
        car_brand: str,
        car_model: str,
        year: str,
        engine_type: str,
        skip: int = 0,
        limit: int = 100,
    ) -> list[ProductResponse]:
        """
        Perform a smart filter search for products based on car compatibility criteria.
        """
        products = (
            self.db.query(Product)
            .join(Compatibility)
            .filter(
                Product.is_active == True,
                Compatibility.is_active == True,
                Compatibility.car_brand.ilike(f"%{car_brand}%"),
                Compatibility.car_model.ilike(f"%{car_model}%"),
                Compatibility.year.ilike(f"%{year}%"),
                Compatibility.engine_type.ilike(f"%{engine_type}%"),
            )
            .offset(skip)
            .limit(limit)
            .all()
        )
        return [ProductResponse.model_validate(p) for p in products]

    def match_ai_identified_part(
        self, ai_label: str, car_brand: str, car_model: str, year: str
    ) -> dict:
        """
        Match AI-identified part labels with compatibility records to find potential product matches.
        """
        # Search for compatibilities that match the car criteria and have products with names similar to the AI label
        query = (
            self.db.query(Product)
            .join(Compatibility)
            .filter(
                Product.is_active == True,
                Compatibility.is_active == True,
                Compatibility.car_brand.ilike(f"%{car_brand}%"),
                Compatibility.car_model.ilike(f"%{car_model}%"),
                Compatibility.year.ilike(f"%{year}%"),
            )
        )

        # Find all products that are compatible with this car
        matches = query.all()

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

        # Fulfill the PDF Edge Case Requirements perfectly
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
