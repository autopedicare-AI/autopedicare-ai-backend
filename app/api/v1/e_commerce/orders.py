from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.db.session import get_db
from app.api.dependencies import get_current_user
from app.schemas.e_commerce.orders import OrderCreate, OrderResponse
from app.models.user import User
from app.services.e_commerce.orders import OrderService

router = APIRouter(prefix="/orders", tags=["orders"])


async def get_order_service(
    db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)
):
    return OrderService(db, current_user)


@router.post("/checkout", response_model=OrderResponse)
async def checkout(
    order_data: OrderCreate, service: OrderService = Depends(get_order_service)
):
    return await service.checkout(order_data)


@router.get("/", response_model=List[OrderResponse])
async def get_my_order(service: OrderService = Depends(get_order_service)):
    return await service.get_user_orders()
