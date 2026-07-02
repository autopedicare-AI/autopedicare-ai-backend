from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from app.core.config import settings


DATABASE_URL = settings.DATABASE_URL.replace(
    "postgresql://",
    "postgresql+asyncpg://"
)

if DATABASE_URL.startswith("sqlite:///") and "+aiosqlite" not in DATABASE_URL:
    DATABASE_URL = DATABASE_URL.replace("sqlite:///", "sqlite+aiosqlite:///")

engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    pool_pre_ping=True,
    pool_size=20,
    max_overflow=40,
    pool_recycle=3600,
    connect_args=(
        {"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {}
    ),
)

AsyncSessionLocal = async_sessionmaker(
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
    bind=engine,
)

SessionLocal = None
if settings.DATABASE_URL.startswith("sqlite:///"):
    sync_engine = create_engine(settings.DATABASE_URL, connect_args={"check_same_thread": False})
    SessionLocal = sessionmaker(bind=sync_engine)


class Base(DeclarativeBase):
    pass


async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
