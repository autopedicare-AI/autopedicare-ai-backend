import uuid
from sqlalchemy import Column, Boolean, String, DateTime, UUID, Enum
from datetime import datetime, timezone
from sqlalchemy.orm import relationship

from app.db.session import Base
from app.permissions.permissions import Role


class User(Base):
    __tablename__ = "users"

    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, index=True, nullable=True)
    role = Column(
        Enum(Role, name="user_role"), nullable=False, default=Role.USER, index=True
    )
    provider = Column(String, nullable=False)
    provider_id = Column(String, unique=True, index=True, nullable=False)
    is_verified = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True
    )

    vendor = relationship(
        "Vendor",
        back_populates="owner",
        uselist=False,
    )

    mechanic = relationship(
        "Mechanic",
        back_populates="user",
        uselist=False,
    )

    driver = relationship(
        "Driver",
        back_populates="user",
        uselist=False,
    )
