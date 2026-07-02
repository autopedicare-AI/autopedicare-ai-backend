import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Column,
    String,
    UUID,
    DateTime,
    Integer,
    Float,
    Boolean,
    ForeignKey,
    Enum,
)

from sqlalchemy.orm import relationship

from app.db.session import Base
from app.models.enums.approval_status import ApprovalStatus


class Driver(Base):
    __tablename__ = "drivers"

    id = Column(UUID, primary_key=True, default=uuid.uuid4)

    user_id = Column(
        UUID,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )

    employee_number = Column(String(50), unique=True)

    phone_number = Column(String(20), nullable=False)

    address = Column(String(255))

    city = Column(String(100))

    state = Column(String(100))

    country = Column(String(100))

    license_number = Column(String(100), nullable=False)

    license_expiry = Column(DateTime(timezone=True))

    current_vehicle_id = Column(
        UUID,
        ForeignKey("vehicles.id"),
        nullable=True,
    )

    availability = Column(String(30), default="OFFLINE")

    current_latitude = Column(Float)

    current_longitude = Column(Float)

    last_location_update = Column(DateTime(timezone=True))

    total_completed_deliveries = Column(Integer, default=0)

    rating = Column(Float, default=0)

    approval_status = Column(
        Enum(ApprovalStatus),
        default=ApprovalStatus.PENDING,
        nullable=False,
    )

    is_active = Column(Boolean, default=True)

    approved_by = Column(
        UUID,
        ForeignKey("users.id"),
    )

    approved_at = Column(DateTime(timezone=True))

    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )

    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    user = relationship(
        "User",
        foreign_keys=[user_id],
        back_populates="driver",
    )
