import uuid
from sqlalchemy import (
    Column,
    Boolean,
    Integer,
    String,
    UUID,
    Float,
    DateTime,
    ForeignKey,
    Index,
)
from datetime import datetime, timezone
from sqlalchemy.orm import relationship
from app.db.session import Base


class Vendor(Base):
    __tablename__ = "vendors"

    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    owner_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, unique=True, index=True
    )
    business_name = Column(String(255), nullable=False, unique=True)
    email = Column(String(255), nullable=True, unique=True)
    phone_number = Column(String(20), nullable=True)
    address = Column(String(255), nullable=True)
    rating = Column(Float, nullable=True, default=0.0)
    delivery_days = Column(Integer, default=3)
    verified = Column(Boolean, default=False, index=True)
    created_at = Column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    owner = relationship("User", back_populates="vendor")
    products = relationship(
        "Product", back_populates="vendor", cascade="all, delete-orphan"
    )
    compatibilities = relationship(
        "Compatibility", back_populates="vendor", cascade="all, delete-orphan"
    )
