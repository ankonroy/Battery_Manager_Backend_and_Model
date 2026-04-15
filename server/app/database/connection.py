"""
Database configuration and connection setup.
"""
import os
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import declarative_base
from sqlalchemy import text
from dotenv import load_dotenv

load_dotenv()

# Get database URL and convert to async format
DATABASE_URL = os.getenv("DATABASE_URL", "")
print(f"🔍 Original DATABASE_URL: {DATABASE_URL}")

if DATABASE_URL:
    DATABASE_URL = DATABASE_URL.replace(
        "postgresql://", "postgresql+asyncpg://"
    )
    if "?sslmode=" in DATABASE_URL:
        DATABASE_URL = DATABASE_URL.split("?")[0]

print(f"🔍 Final DATABASE_URL: {DATABASE_URL}")

# Create async engine with SMALL connection pool
engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    pool_size=3,        # Reduced for Render free tier
    max_overflow=5,
    pool_recycle=3600,
    pool_pre_ping=True,
)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# Base class for models
Base = declarative_base()


async def get_db():
    """Dependency for FastAPI endpoints."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def check_database_connection() -> bool:
    """Verify database connection."""
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False