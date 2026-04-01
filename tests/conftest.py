import os
# Set DATABASE_URL to SQLite file-based for testing (so it's shared across connections)
os.environ["DATABASE_URL"] = "sqlite:///test_db.db"

import pytest
import time
from loguru import logger
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.api.dependencies import Base



@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    """Set up test database using SQLite file-based"""
    # Use SQLite file-based for testing (shared across connections)
    test_database_url = "sqlite:///test_db.db"

    # Create engine and test connection
    test_engine = create_engine(test_database_url)
    
    # Test connection
    with test_engine.connect() as conn:
        conn.execute(text("SELECT 1"))

    # Create all tables
    Base.metadata.create_all(bind=test_engine)

    # DATABASE_URL is already set at the top of this file

    yield

    # Cleanup - drop all tables and remove the file
    Base.metadata.drop_all(bind=test_engine)
    test_engine.dispose()
    
    # Remove the test database file
    import os
    if os.path.exists("test.db"):
        os.remove("test.db")


@pytest.fixture(autouse=True)
def mock_geo_service(monkeypatch):
    """Mock the geo service to avoid external API calls during tests"""
    async def mock_get_location_from_ip(ip: str):
        return {
            "country": "US",
            "state": "CA",
            "city": "San Francisco",
            "latitude": 37.7749,
            "longitude": -122.4194,
        }
    
    monkeypatch.setattr("app.services.geo.get_location_from_ip", mock_get_location_from_ip)


@pytest.fixture
def db_session():
    """Provide a database session for testing"""
    from app.api.dependencies import SessionLocal
    db = SessionLocal()
    try:
        yield db
    finally:
        db.rollback()


@pytest.fixture
def auth_headers():
    """Generate valid JWT auth headers for testing protected endpoints"""
    from app.core.security import create_access_token
    from app.models.user import User
    from app.api.dependencies import SessionLocal
    import uuid

    db = SessionLocal()
    try:
        unique_suffix = uuid.uuid4().hex
        user = User(
            email=f"test+{unique_suffix}@autopedicare.com",
            provider="google",
            provider_id=str(uuid.uuid4()),
            is_verified=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        access_token = create_access_token({"sub": str(user.id)})
        return {"Authorization": f"Bearer {access_token}"}
    finally:
        db.close()
        db.close()
