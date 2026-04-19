from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from loguru import logger

from app.models.e_commerce.vendors import Vendor
from app.models.user import User
from app.schemas.e_commerce.vendors import VendorCreate, VendorUpdate, VendorResponse


class VendorService:
    def __init__(self, db: Session, current_user: User):
        self.db = db
        self.current_user = current_user

    def create_vendor(self, vendor_data: VendorCreate) -> VendorResponse:
        existing_vendor = (
            self.db.query(Vendor)
            .filter(Vendor.owner_id == self.current_user.id)
            .first()
        )
        if existing_vendor:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Vendor profile already exists for this user.",
            )

        vendor_dict = vendor_data.model_dump()
        vendor_dict["owner_id"] = self.current_user.id

        vendor = Vendor(**vendor_dict)
        self.db.add(vendor)
        try:
            self.db.commit()
            self.db.refresh(vendor)
            return VendorResponse.model_validate(vendor)
        except Exception:
            self.db.rollback()
            logger.exception(
                "Vendor create error",
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error",
            )

    def get_vendor_by_id(self) -> VendorResponse:
        vendor = (
            self.db.query(Vendor)
            .filter(Vendor.owner_id == self.current_user.id)
            .first()
        )
        if not vendor:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Vendor not found",
            )
        return VendorResponse.model_validate(vendor)

    def update_vendor(self, vendor_data: VendorUpdate) -> VendorResponse:
        vendor = (
            self.db.query(Vendor)
            .filter(Vendor.owner_id == self.current_user.id)
            .first()
        )
        if not vendor:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Vendor not found",
            )

        update_data = vendor_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(vendor, field, value)

        try:
            self.db.commit()
            self.db.refresh(vendor)
            return VendorResponse.model_validate(vendor)
        except Exception:
            self.db.rollback()
            logger.exception(
                "Vendor update error",
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error",
            )

    def delete_vendor(self):
        vendor = (
            self.db.query(Vendor)
            .filter(Vendor.owner_id == self.current_user.id)
            .first()
        )
        if not vendor:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Vendor not found",
            )
        self.db.delete(vendor)
        try:
            self.db.commit()
        except Exception:
            self.db.rollback()
            logger.exception(
                "Vendor delete error",
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error",
            )

    def list_all_vendors(self) -> list[VendorResponse]:
        vendors = self.db.query(Vendor).all()
        return [VendorResponse.model_validate(vendor) for vendor in vendors]

    def get_vendor_by_user_id(self, vendor_id: str) -> VendorResponse:
        vendor = self.db.query(Vendor).filter(Vendor.owner_id == vendor_id).first()
        if not vendor:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Vendor not found",
            )
        return VendorResponse.model_validate(vendor)
