import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Column,
    String,
    Boolean,
    DateTime,
    UUID,
    ForeignKey,
    Float,
    Integer,
    Enum,
)
from sqlalchemy.orm import relationship

from app.db.session import Base
from app.models.enums.approval_status import ApprovalStatus


class Vendor(Base):
    __tablename__ = "vendors"

    id = Column(UUID, primary_key=True, default=uuid.uuid4)

    owner_id = Column(
        UUID,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )

    business_name = Column(String(255), nullable=False)
    business_email = Column(String(255), nullable=True)
    business_phone = Column(String(20), nullable=False)

    business_address = Column(String(255))
    city = Column(String(100))
    state = Column(String(100))
    country = Column(String(100))

    registration_number = Column(String(100))
    tax_number = Column(String(100))

    logo_url = Column(String(500))
    banner_url = Column(String(500))

    description = Column(String)

    rating = Column(Float, default=0)
    total_reviews = Column(Integer, default=0)

    approval_status = Column(
        Enum(ApprovalStatus),
        default=ApprovalStatus.PENDING,
        nullable=False,
    )

    is_active = Column(Boolean, default=True)

    approved_by = Column(
        UUID,
        ForeignKey("users.id"),
        nullable=True,
    )

    approved_at = Column(DateTime(timezone=True))
    suspended_at = Column(DateTime(timezone=True))

    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )

    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    owner = relationship(
        "User",
        foreign_keys=[owner_id],
        back_populates="vendor",
    )
