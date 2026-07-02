from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.db.session import get_db
from app.models.user import User
from app.api.dependencies import get_current_user
from app.services.e_commerce.compatibilities import CompatibilityService
from app.schemas.e_commerce.compatibility import (
    CompatibilityCreate,
    CompatibilityResponse,
    CompatibilityUpdate,
)

router = APIRouter(prefix="/compatibilities", tags=["Compatibilities"])


async def get_compatibilites_service(
    db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)
):
    return CompatibilityService(db, current_user)


@router.post(
    "/", response_model=CompatibilityResponse, status_code=status.HTTP_201_CREATED
)
async def create_compatibility(
    compatibility_data: CompatibilityCreate,
    service: CompatibilityService = Depends(get_compatibilites_service),
):
    return await service.create_compatibility(compatibility_data)


@router.get("/{compatibility_id}", response_model=CompatibilityResponse)
async def get_compatibility_by_id(
    compatibility_id: UUID,
    service: CompatibilityService = Depends(get_compatibilites_service),
):
    return await service.get_compatibility(compatibility_id)


@router.put("/{compatibility_id}", response_model=CompatibilityResponse)
async def update_compatibility(
    compatibility_id: UUID,
    compatibility_data: CompatibilityUpdate,
    service: CompatibilityService = Depends(get_compatibilites_service),
):
    return await service.update_compatibility(compatibility_id, compatibility_data)


@router.delete("/{compatibility_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_compatibility(
    compatibility_id: UUID,
    service: CompatibilityService = Depends(get_compatibilites_service),
):
    await service.delete_compatibility(compatibility_id)
    return None


@router.get("/product/{product_id}", response_model=list[CompatibilityResponse])
async def get_compatibilities_by_product(
    product_id: UUID,
    service: CompatibilityService = Depends(get_compatibilites_service),
):
    return await service.get_compatibilities_by_product(product_id)


@router.post("/search", response_model=list[CompatibilityResponse])
async def smart_filter_search(
    car_brand: str,
    car_model: str,
    year: str,
    engine_type: str,
    service: CompatibilityService = Depends(get_compatibilites_service),
):
    return await service.smart_filter_search(
        car_brand, car_model, year, engine_type, skip=0, limit=100
    )


@router.post("/match-scanned-part", response_model=list[CompatibilityResponse])
async def match_ai_identified_part(
    ai_label: str,
    car_brand: str,
    car_model: str,
    year: str,
    service: CompatibilityService = Depends(get_compatibilites_service),
):
    return await service.match_ai_identified_part(ai_label, car_brand, car_model, year)
