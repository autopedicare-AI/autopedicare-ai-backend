from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.db.session import get_db
from app.api.dependencies import get_current_user
from app.models.user import User
from app.services.e_commerce.carts import CartService
from app.schemas.e_commerce.carts import CartResponse, CartItemCreate, CartItemUpdate

router = APIRouter(prefix="/cart", tags=["Cart"])


async def get_cart_service(
    db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)
):
    return CartService(db, current_user)


@router.get("/", response_model=CartResponse)
async def view_cart(service: CartService = Depends(get_cart_service)):
    """View the current user's cart."""
    return await service.view_cart()


@router.post("/items", response_model=CartResponse)
async def add_to_cart(
    cart_data: CartItemCreate, service: CartService = Depends(get_cart_service)
):
    """Add an item to the cart."""
    return await service.add_to_cart(cart_data)


@router.put("/items/{item_id}", response_model=CartResponse)
async def update_cart_item(
    item_id: UUID,
    cart_data: CartItemUpdate,
    service: CartService = Depends(get_cart_service),
):
    """Update the quantity of an item in the cart."""
    return await service.update_cart_item(item_id, cart_data)


@router.delete("/items/{item_id}", response_model=CartResponse)
async def remove_cart_item(
    item_id: UUID, service: CartService = Depends(get_cart_service)
):
    """Remove an item from the cart."""
    return await service.remove_cart_item(item_id)
