import uuid
from sqlalchemy import Column, String, ForeignKey, UUID, DateTime, Boolean, Integer
from datetime import datetime, timezone
from sqlalchemy.orm import relationship
from app.db.session import Base


class ProductImage(Base):
    __tablename__ = "product_images"

    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    product_id = Column(
        UUID, ForeignKey("products.id", ondelete="CASCADE"), nullable=False
    )
    image_url = Column(String, nullable=False)
    angle_type = Column(String(50), nullable=False)
    display_order = Column(Integer, default=1, nullable=False)
    is_primary = Column(Boolean, default=False)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    product = relationship("Product", back_populates="images")
