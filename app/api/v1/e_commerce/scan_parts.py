from fastapi import APIRouter, Depends, UploadFile, File, status, Form
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.api.dependencies import get_current_user
from app.models.user import User
from app.services.e_commerce.compatibilities import CompatibilityService


router = APIRouter()


async def get_compatibility_service(
    db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)
):
    return CompatibilityService(db, user)


@router.post("/scan-parts")
async def scan_and_match_parts(
    file: UploadFile = File(...),
    car_brand: str = Form(...),
    car_model: str = Form(...),
    year: str = Form(...),
    service: CompatibilityService = Depends(get_compatibility_service),
):

    # Calling AI service to process the image and extract labels
    # ai_label = await service.process_image_and_extract_labels(file)
    ai_label = "Brake part"

    # Matching extracted labels with products in the database
    results = await service.match_ai_identified_part(
        ai_label=ai_label, car_brand=car_brand, car_model=car_model, year=year
    )

    return {"matches": results}
