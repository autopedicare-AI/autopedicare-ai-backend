from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from app.models.e_commerce.vendors import Vendor
from app.models.user import User
from app.schemas.e_commerce.vendors import VendorCreate, VendorUpdate, VendorResponse


class VendorService:
    def __init__(self, db: AsyncSession, current_user: User):
        self.db = db
        self.current_user = current_user

    async def create_vendor(self, vendor_data: VendorCreate) -> VendorResponse:
        result = await self.db.execute(
            select(Vendor).where(Vendor.owner_id == self.current_user.id)
        )
        existing_vendor = result.scalars().first()
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
            await self.db.commit()
            await self.db.refresh(vendor)
            return VendorResponse.model_validate(vendor)
        except Exception:
            await self.db.rollback()
            logger.exception(
                "Vendor create error",
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error",
            )

    async def get_vendor_by_id(self) -> VendorResponse:
        result = await self.db.execute(
            select(Vendor).where(Vendor.owner_id == self.current_user.id)
        )
        vendor = result.scalars().first()
        if not vendor:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Vendor not found",
            )
        return VendorResponse.model_validate(vendor)

    async def update_vendor(self, vendor_data: VendorUpdate) -> VendorResponse:
        result = await self.db.execute(
            select(Vendor).where(Vendor.owner_id == self.current_user.id)
        )
        vendor = result.scalars().first()
        if not vendor:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Vendor not found",
            )

        update_data = vendor_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(vendor, field, value)

        try:
            await self.db.commit()
            await self.db.refresh(vendor)
            return VendorResponse.model_validate(vendor)
        except Exception:
            await self.db.rollback()
            logger.exception(
                "Vendor update error",
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error",
            )

    async def delete_vendor(self):
        result = await self.db.execute(
            select(Vendor).where(Vendor.owner_id == self.current_user.id)
        )
        vendor = result.scalars().first()
        if not vendor:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Vendor not found",
            )
        await self.db.delete(vendor)
        try:
            await self.db.commit()
        except Exception:
            await self.db.rollback()
            logger.exception(
                "Vendor delete error",
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error",
            )

    async def list_all_vendors(self, skip: int = 0, limit: int = 10) -> list[VendorResponse]:
        result = await self.db.execute(select(Vendor).offset(skip).limit(limit))
        vendors = result.scalars().all()
        return [VendorResponse.model_validate(vendor) for vendor in vendors]

    async def get_vendor_by_user_id(self, vendor_id: str) -> VendorResponse:
        result = await self.db.execute(
            select(Vendor).where(Vendor.owner_id == vendor_id)
        )
        vendor = result.scalars().first()
        if not vendor:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Vendor not found",
            )
        return VendorResponse.model_validate(vendor)
