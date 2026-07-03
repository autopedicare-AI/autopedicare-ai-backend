import hashlib
import httpx
import uuid
import hmac
import json
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from loguru import logger

from app.core.config import settings
from app.models.e_commerce.orders import Order, OrderStatus


class PaystackService:
    def __init__(self, db: AsyncSession, current_user=None):
        self.db = db
        self.current_user = current_user
        self.secret_key = settings.PAYSTACK_SECRET_KEY
        self.base_url = settings.PAYSTACK_BASE_URL
        self.headers = {
            "Authorization": f"Bearer {self.secret_key}",
            "Content-Type": "application/json",
        }

    async def initialize_payment(self, order_id: str, callback_url: str = None):
        """Generate payment link with strict idempotency"""
        result = await self.db.execute(
            select(Order).where(Order.id == order_id, Order.user_id == self.current_user.id)
        ).with_for_update()
        order = result.scalars().first()

        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Order not found"
            )

        if order.status != OrderStatus.PENDING or order.payment_status == "paid":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Order is already paid"
            )

        if order.payment_reference and order.authorization_url:
            return {
                "authorization_url": order.authorization_url,
                "reference": order.payment_reference,
                "message": "Retrieved existing payment session",
            }

        # Generating a new unique reference
        transaction_reference = f"ORD-{uuid.uuid4().hex[:12].upper()}"
        amount_in_kobo = int(order.total_amount * 100)

        final_callback_url = callback_url or settings.JWT_AUDIENCE

        payload = {
            "email": self.current_user.email,
            "amount": amount_in_kobo,
            "reference": transaction_reference,
            "callback_url": final_callback_url,
        }

        timeout = httpx.Timeout(10.0, connect=3.0) 
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(
                f"{self.base_url}/transaction/initialize",
                headers=self.headers,
                json=payload,
            )

        if response.status_code != 200:
            logger.error("Paystack init Error: {error}", error=response.text)
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Failed to initialize payment gateway",
            )

        response_data = response.json()
        authorization_url = response_data["data"]["authorization_url"]

        order.payment_reference = transaction_reference
        order.authorization_url = authorization_url
        await self.db.commit()

        return {
            "authorization_url": authorization_url,
            "reference": transaction_reference,
            "message": "Created new payment session",
        }

    async def verify_payment(self, reference: str):
        """Manual verification (when user is redirected back to the frontend)."""
        timeout = httpx.Timeout(10.0, connect=3.0)
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.get(
                f"{self.base_url}/transaction/verify/{reference}", headers=self.headers
            )

        if response.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid transaction reference",
            )

        response_data = response.json()
        paystack_status = response_data["data"]["status"]

        order = (
            await self.db.execute(select(Order).where(Order.payment_reference == reference))
        ).scalars().first()
        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Order associated with this payment not found",
            )

        if paystack_status == "success" and order.payment_status != "paid":
            order.payment_status = "paid"
            order.status = OrderStatus.PAID
            await self.db.commit()

        return {
            "status": order.payment_status,
            "message": (
                "Payment verified successfully"
                if paystack_status == "success"
                else "Payment pending or failed"
            ),
        }

    async def process_webhook(self, payload: bytes, signature: str):
        """
        Automated background verification by Paystack.
        Capture payments incase user closes their browser
        """
        if not signature:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing signature header",
            )

        # verifying the signature cryptographically
        expected_signature = hmac.new(
            key=self.secret_key.encode("utf-8"), msg=payload, digestmod=hashlib.sha512
        ).hexdigest()

        if expected_signature != signature:
            logger.warning("Attempted Webhook Hack: Invalid Signature")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid signature"
            )

        try:
            data = json.loads(payload)
        except json.JSONDecodeError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid JSON payload"
            )

        # Handle "charge.success" event
        event = data.get("event")
        if event == "charge.success":
            reference = data["data"]["reference"]

            order = (
                await self.db.execute(
                    select(Order).where(Order.payment_reference == reference)
                )
            ).scalars().first()
            if order and order.payment_status != "paid":
                order.payment_status = "paid"
                order.status = OrderStatus.PAID
                await self.db.commit()
                logger.info(
                    "Order {order_id} marked as PAID via Webhook.", order_id=order.id
                )

        return {"status": "success"}
