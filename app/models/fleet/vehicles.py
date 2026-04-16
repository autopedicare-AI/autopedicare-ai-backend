import uuid
from sqlalchemy import Column, String, Integer, Enum, DateTime, UUID
from datetime import datetime, timezone
from app.db.session import Base
import enum


class VehicleStatus(enum.Enum):
    active = "active"
    maintenance = "maintenance"
    inactive = "inactive"


class Vehicle(Base):
    __tablename__ = "vehicles"

    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    plate_number = Column(String, unique=True, nullable=False)
    model = Column(String, nullable=False)
    manufacturer = Column(String, nullable=False)
    year = Column(Integer, nullable=False)
    vehicle_type = Column(String, nullable=False)
    status = Column(
        Enum(VehicleStatus, name="vehiclestatus", create_type=False), 
        default=VehicleStatus.active, 
        nullable=False
    )
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))