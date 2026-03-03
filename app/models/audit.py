import uuid
from sqlalchemy import Column, String, DateTime, Float, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime, timezone
from app.api.dependencies import Base


class UserLoginHistory(Base):
    __tablename__ = "user_login_history"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    ip_address = Column(String)
    device = Column(String)
    os = Column(String)
    browser = Column(String)
    latitude = Column(Float)
    longitude = Column(Float)
    country = Column(String)
    city = Column(String)
    provider = Column(String)
    user_agent = Column(String)
    logged_in_at = Column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
