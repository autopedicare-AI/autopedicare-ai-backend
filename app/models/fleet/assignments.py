import uuid
from sqlalchemy import Column, Enum, ForeignKey, DateTime, UUID
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.db.session import Base
import enum


class AssignmentStatus(enum.Enum):
    active = "active"
    inactive = "inactive"


class Assignment(Base):
    __tablename__ = "assignments"

    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    driver_id = Column(UUID, ForeignKey("drivers.id"), nullable=False)
    vehicle_id = Column(UUID, ForeignKey("vehicles.id"), nullable=False)
    assigned_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    status = Column(Enum(AssignmentStatus), default=AssignmentStatus.active, nullable=False)

    # Relationships
    driver = relationship("Driver", backref="assignments")
    vehicle = relationship("Vehicle", backref="assignments")