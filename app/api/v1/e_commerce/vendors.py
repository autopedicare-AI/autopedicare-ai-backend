from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.api.dependencies import get_current_user
from app.schemas.e_commerce.vendors import VendorCreate, VendorResponse, VendorUpdate
from app.services.e_commerce.vendors import VendorService
from app.models.user import User


router = APIRouter(prefix="/vendors", tags=["Vendors"])


async def get_vendor_service(
    db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)
):
    return VendorService(db, current_user)


@router.post("/", response_model=VendorResponse, status_code=status.HTTP_201_CREATED)
async def create_vendor(
    vendor_data: VendorCreate, service: VendorService = Depends(get_vendor_service)
):
    return await service.create_vendor(vendor_data)


@router.get("/", response_model=VendorResponse)
async def get_vendors(service: VendorService = Depends(get_vendor_service)):
    return await service.get_vendor_by_id()


@router.put("/", response_model=VendorResponse)
async def update_vendor(
    vendor_data: VendorUpdate, service: VendorService = Depends(get_vendor_service)
):
    return await service.update_vendor(vendor_data)

@router.delete("/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_vendor(service: VendorService = Depends(get_vendor_service)):
    await service.delete_vendor()
    return None