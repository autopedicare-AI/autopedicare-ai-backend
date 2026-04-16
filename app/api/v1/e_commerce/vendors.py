from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.api.dependencies import get_current_user
from app.schemas.e_commerce.vendors import VendorCreate, VendorResponse, VendorUpdate
from app.services.e_commerce.vendors import VendorService
from app.models.user import User


router = APIRouter(prefix="/vendors", tags=["Vendors"])


def get_vendor_service(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    return VendorService(db, current_user)


@router.post("/", response_model=VendorResponse, status_code=status.HTTP_201_CREATED)
def create_vendor(
    vendor_data: VendorCreate, service: VendorService = Depends(get_vendor_service)
):
    return service.create_vendor(vendor_data)


@router.get("/", response_model=VendorResponse)
def get_vendors(service: VendorService = Depends(get_vendor_service)):
    return service.get_vendor_by_id()


@router.put("/", response_model=VendorResponse)
def update_vendor(
    vendor_data: VendorUpdate, service: VendorService = Depends(get_vendor_service)
):
    return service.update_vendor(vendor_data)


@router.delete("/", status_code=status.HTTP_204_NO_CONTENT)
def delete_vendor(service: VendorService = Depends(get_vendor_service)):
    service.delete_vendor()
