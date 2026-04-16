from fastapi import HTTPException, status
from typing import List
from sqlalchemy.orm import Session
from loguru import logger
from decimal import Decimal

from app.models.e_commerce.carts import Cart
from app.schemas.e_commerce.orders import OrderCreate, OrderResponse
from app.models.user import User
from app.models.e_commerce.products import Product
from app.models.e_commerce.orders import Order, OrderItem, OrderStatus


class OrderService:
    def __init__(self, db: Session, current_user: User):
        self.db = db
        self.current_user = current_user

    def checkout(self, order_data: OrderCreate) -> OrderResponse:
        """ """
        # fetch user's cart
        cart = self.db.query(Cart).filter(Cart.user_id == self.current_user.id).first()
        if not cart or not cart.items:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cart is empty. Add items before checkout.",
            )

        total_amount = Decimal("0.0")
        order_items = []

        # verify stock
        for cart_item in cart.items:
            product = (
                self.db.query(Product)
                .filter(Product.id == cart_item.product_id)
                .with_for_update()
                .first()
            )

            if not product or not product.is_active:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Product is no longer available",
                )

            if cart_item.quantity > product.stock_quantity:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Not enough stock for {product.name}. Only {product.stock_quantity} left.",
                )

            unit_price = Decimal(str(product.price))
            sub_total = unit_price * cart_item.quantity
            total_amount += sub_total

            order_items.append(
                OrderItem(
                    product_id=product.id,
                    quantity=cart_item.quantity,
                    unit_price=unit_price,
                    sub_total=sub_total,
                )
            )

            # deducting product quantity
            product.stock_quantity -= cart_item.quantity

        # creating order
        new_order = Order(
            user_id=self.current_user.id,
            total_amount=total_amount,
            shipping_address=order_data.shipping_address,
            status=OrderStatus.PENDING,
            payment_status="unpaid",
        )

        self.db.add(new_order)
        self.db.flush()  # getting new order_id without fully commiting yet

        # attaching items to order
        for item in order_items:
            item.order_id = new_order.id
            self.db.add(item)

        # clear cart
        for cart_item in cart.items:
            self.db.delete(cart_item)

        try:
            self.db.commit()
            self.db.refresh(new_order)
            return OrderResponse.model_validate(new_order)
        except Exception as e:
            self.db.rollback()
            logger.error("An error occurred while checking out: {error}", error=e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error",
            )

    def get_user_orders(self) -> List[OrderResponse]:
        """Allow users to see their order history"""
        orders = (
            self.db.query(Order)
            .filter(Order.user_id == self.current_user.id)
            .order_by(Order.created_at.desc())
            .all()
        )
        return [OrderResponse.model_validate(order) for order in orders]
