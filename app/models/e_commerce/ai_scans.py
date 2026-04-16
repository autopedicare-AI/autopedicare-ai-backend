import uuid
from sqlalchemy import Column, String, Float, UUID, ForeignKey, DateTime
from datetime import datetime, timezone
from app.db.session import Base


class AIScan(Base):
    __tablename__ = "ai_scans"

    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID, ForeignKey("users.id"), nullable=False)
    image_url = Column(String, nullable=False)
    predicted_part = Column(String, nullable=False)
    confidence_score = Column(Float, nullable=False)
    scan_result = Column(String, nullable=False)
    created_at = Column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
