from fastapi import APIRouter, Depends, Request, Header, BackgroundTasks, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.api.dependencies import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.services.payment.payment import PaystackService

router = APIRouter(tags=["Payments"])


def get_paystack_service(
    db: AsyncSession = Depends(get_db), current_user: Optional[User] = None
):
    return PaystackService(db, current_user)


@router.post("/pay/{order_id}")
async def initialize_payment(
    order_id: str,
    callback_url: Optional[str] = Query(None, description="Mobile app deep link or web redirect URL"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Generate or retrieves the Paystack checkout URL for an order"""
    service = get_paystack_service(db, current_user)
    return await service.initialize_payment(order_id, callback_url)


@router.get("/pay/verify/{reference}")
async def verify_payment(
    reference: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Verififes a payment reference after the user returns from Paystack."""
    service = get_paystack_service(db, current_user)
    return await service.verify_payment(reference)


@router.post("/pay/webhook")
async def paystack_webhook(
    request: Request,
    x_paystack_signature: str = Header(None),
    db: AsyncSession = Depends(get_db)
):
    """
    Paystack Webhook Endpoint.
    This receives background updates directly from Paystack's servers.
    NO USER AUTHENTICATION APPLIES HERE. Security is handled via HMAC signature.
    """
    payload = await request.body()
    
    service = get_paystack_service(db=db, current_user=None)
    
    return await service.process_webhook(payload, x_paystack_signature)