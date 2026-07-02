import uuid
from sqlalchemy import Column, String, Float, Enum, ForeignKey, DateTime, UUID
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.db.session import Base
import enum


class TripStatus(enum.Enum):
    ongoing = "ongoing"
    completed = "completed"
    cancelled = "cancelled"


class Trip(Base):
    __tablename__ = "trips"

    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    driver_id = Column(UUID, ForeignKey("drivers.id"), nullable=False)
    vehicle_id = Column(UUID, ForeignKey("vehicles.id"), nullable=False)
    start_location = Column(String, nullable=False)
    end_location = Column(String, nullable=False)
    start_time = Column(DateTime(timezone=True), nullable=False)
    end_time = Column(DateTime(timezone=True), nullable=True)
    distance_km = Column(Float, nullable=False)
    status = Column(
        Enum(TripStatus, name="tripstatus", create_type=False),
        default=TripStatus.ongoing,
        nullable=False,
    )

    # Relationships
    driver = relationship("Driver", backref="trips")
    vehicle = relationship("Vehicle", backref="trips")