from uuid import UUID
from decimal import Decimal
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from loguru import logger

from app.models.e_commerce.carts import Cart, CartItem
from app.schemas.e_commerce.carts import CartItemCreate, CartItemUpdate
from app.models.user import User
from app.models.e_commerce.products import Product


class CartService:
    def __init__(self, db: Session, current_user: User):
        self.db = db
        self.current_user = current_user
        self.cart = self._get_or_create_cart()

    def _get_or_create_cart(self) -> Cart:
        cart = self.db.query(Cart).filter(Cart.user_id == self.current_user.id).first()
        if not cart:
            cart = Cart(user_id=self.current_user.id)
            self.db.add(cart)
            self.db.commit()
            self.db.refresh(cart)
        return cart

    def add_to_cart(self, cart_data: CartItemCreate):
        try:
            product = (
                self.db.query(Product)
                .filter(Product.id == cart_data.product_id, Product.is_active == True)
                .with_for_update()
                .first()
            )

            if not product:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Product not found or unavailable.",
                )

            # Check if the item is already in the cart
            existing_cart_item = (
                self.db.query(CartItem)
                .filter(
                    CartItem.cart_id == self.cart.id,
                    CartItem.product_id == cart_data.product_id,
                )
                .first()
            )

            new_quantity = cart_data.quantity
            if existing_cart_item:
                new_quantity += existing_cart_item.quantity

            # stock validation
            if new_quantity > product.stock_quantity:
                available_stock = product.stock_quantity - (
                    existing_cart_item.quantity if existing_cart_item else 0
                )
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Only {available_stock} more units can be added. Current stock: {product.stock_quantity}.",
                )

            if existing_cart_item:
                existing_cart_item.quantity = new_quantity
            else:
                new_cart_item = CartItem(
                    cart_id=self.cart.id,
                    product_id=cart_data.product_id,
                    quantity=cart_data.quantity,
                )
                self.db.add(new_cart_item)

            self.db.commit()
            return self.view_cart()

        except HTTPException:
            raise
        except Exception as e:
            self.db.rollback()
            logger.error("Error adding to cart: {error}", error=e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="An error occurred while adding the item to the cart. Please try again.",
            )

    def view_cart(self):
        items_response = []
        cart_total = Decimal("0.00")

        for item in self.cart.items:
            unit_price = item.product.price
            sub_total = unit_price * item.quantity
            cart_total += sub_total

            items_response.append(
                {
                    "id": item.id,
                    "product_id": item.product_id,
                    "quantity": item.quantity,
                    "product_name": item.product.name,
                    "product_price": unit_price,
                    "subtotal": sub_total,
                }
            )
        return {
            "id": self.cart.id,
            "user_id": self.cart.user_id,
            "items": items_response,
            "total_amount": cart_total,
        }

    def update_cart_item(self, item_id: UUID, cart_data: CartItemUpdate):
        try:
            cart_item = (
                self.db.query(CartItem)
                .filter(CartItem.id == item_id, CartItem.cart_id == self.cart.id)
                .with_for_update()
                .first()
            )

            if not cart_item:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Cart item not found.",
                )

            if cart_data.quantity <= 0:
                return self.remove_cart_item(item_id)

            if cart_data.quantity > cart_item.product.stock_quantity:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Only {cart_item.product.stock_quantity} units available in stock.",
                )

            cart_item.quantity = cart_data.quantity
            self.db.commit()
            return self.view_cart()

        except HTTPException:
            raise
        except Exception as e:
            self.db.rollback()
            logger.error("Error updating cart item: {error}", error=e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="An error occurred while updating the cart item. Please try again.",
            )

    def remove_cart_item(self, item_id: UUID):
        try:
            cart_item = (
                self.db.query(CartItem)
                .filter(CartItem.id == item_id, CartItem.cart_id == self.cart.id)
                .first()
            )

            if not cart_item:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Cart item not found.",
                )

            self.db.delete(cart_item)
            self.db.commit()
            return self.view_cart()

        except HTTPException:
            raise
        except Exception as e:
            self.db.rollback()
            logger.error("Error removing cart item: {error}", error=e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="An error occurred while removing the cart item. Please try again.",
            )
