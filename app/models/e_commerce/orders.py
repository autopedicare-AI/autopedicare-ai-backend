import uuid
from sqlalchemy import Column, String, DECIMAL, UUID, ForeignKey, DateTime, Integer
from datetime import datetime, timezone
from sqlalchemy.orm import relationship
from app.db.session import Base


class OrderStatus:
    PENDING = "pending"
    PAID = "paid"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


class Order(Base):
    __tablename__ = "orders"

    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    status = Column(String, nullable=False, default=OrderStatus.PENDING)
    total_amount = Column(DECIMAL(10, 2), nullable=False)
    payment_status = Column(String, nullable=False, default="unpaid")
    payment_reference = Column(String, nullable=True)
    shipping_address = Column(String, nullable=False)
    authorization_url = Column(String, nullable=True)
    created_at = Column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    items = relationship(
        "OrderItem", back_populates="order", cascade="all, delete-orphan"
    )


class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    order_id = Column(UUID, ForeignKey("orders.id", ondelete="CASCADE"), nullable=False)
    product_id = Column(
        UUID, ForeignKey("products.id", ondelete="SET NULL"), nullable=True
    )
    quantity = Column(Integer, nullable=False)
    unit_price = Column(DECIMAL(10, 2), nullable=False)
    sub_total = Column(DECIMAL(10, 2), nullable=False)

    order = relationship("Order", back_populates="items")
    product = relationship("Product")
