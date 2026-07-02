import uuid
from sqlalchemy import Column, String, Enum, DateTime, UUID
from datetime import datetime, timezone
from app.db.session import Base
import enum


class DriverStatus(enum.Enum):
    active = "active"
    inactive = "inactive"


class Driver(Base):
    __tablename__ = "drivers"

    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    full_name = Column(String, nullable=False)
    license_number = Column(String, unique=True, nullable=False)
    phone_number = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    status = Column(
        Enum(DriverStatus, name="driverstatus", create_type=False),
        default=DriverStatus.active,
        nullable=False,
    )
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))