import uuid
from sqlalchemy import (
    DECIMAL,
    Column,
    Boolean,
    String,
    DateTime,
    UUID,
    ForeignKey,
    Integer,
    Index,
)
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.db.session import Base


class Product(Base):
    __tablename__ = "products"
    __table_args__ = (
        Index("ix_products_vendor_id_is_active", "vendor_id", "is_active"),
        Index("ix_products_category_is_active", "category", "is_active"),
        Index("ix_products_created_at_is_active", "created_at", "is_active"),
        Index("ix_products_created_at", "created_at"),
    )

    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False, index=True)
    description = Column(String(255), nullable=True)
    category = Column(String(255), nullable=False, index=True)
    price = Column(DECIMAL(10, 2), nullable=False)
    currency = Column(String(10), default="NGN", nullable=False)
    stock_quantity = Column(Integer, nullable=False)
    oem_number = Column(String(255), nullable=True, unique=True, index=True)
    brand = Column(String(255), nullable=True)
    model = Column(String(255), nullable=True)
    year_from = Column(String(4), nullable=True)
    year_to = Column(String(4), nullable=True)
    is_active = Column(Boolean, default=True)
    vendor_id = Column(
        UUID, ForeignKey("vendors.id", ondelete="CASCADE"), nullable=False, index=True
    )
    created_at = Column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    vendor = relationship("Vendor", back_populates="products")
    images = relationship("ProductImage", back_populates="product")
    compatibilities = relationship(
        "Compatibility", back_populates="product", cascade="all, delete-orphan"
    )
