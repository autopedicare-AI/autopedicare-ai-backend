import uuid
from sqlalchemy import Column, UUID, ForeignKey, DateTime, Integer
from datetime import datetime, timezone
from sqlalchemy.orm import relationship
from app.db.session import Base


class Cart(Base):
    __tablename__ = "carts"

    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    user_id = Column(
        UUID, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    created_at = Column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    items = relationship(
        "CartItem", back_populates="cart", cascade="all, delete-orphan"
    )


class CartItem(Base):
    __tablename__ = "cart_items"

    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    cart_id = Column(UUID, ForeignKey("carts.id", ondelete="CASCADE"), nullable=False)
    product_id = Column(
        UUID, ForeignKey("products.id", ondelete="CASCADE"), nullable=False
    )
    quantity = Column(Integer, nullable=False, default=1)

    cart = relationship("Cart", back_populates="items")
    product = relationship("Product")
