import uuid
from sqlalchemy import Column, String, UUID, ForeignKey, DateTime, Boolean, Index
from datetime import datetime, timezone
from app.db.session import Base
from sqlalchemy.orm import relationship


class Compatibility(Base):
    __tablename__ = "compatibilities"
    __table_args__ = (
        Index("ix_compatibilities_vendor_id_is_active", "vendor_id", "is_active"),
        Index("ix_compatibilities_created_at_is_active", "created_at", "is_active"),
    )

    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    product_id = Column(
        UUID, ForeignKey("products.id", ondelete="CASCADE"), nullable=False
    )
    vendor_id = Column(UUID, ForeignKey("vendors.id"), nullable=False, index=True)
    car_brand = Column(String(255), nullable=False)
    car_model = Column(String(255), nullable=False)
    year = Column(String(4), nullable=True)
    engine_type = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    product = relationship("Product", back_populates="compatibilities")
    vendor = relationship("Vendor", back_populates="compatibilities")
