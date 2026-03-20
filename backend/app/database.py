"""
Database connection and session management.
Uses SQLAlchemy async with PostgreSQL (provided by Railway).
"""

import os
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

# Railway automatically provides DATABASE_URL in the environment
DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql+asyncpg://user:password@localhost/emailhub")

# Railway sometimes provides postgres:// instead of postgresql+asyncpg://
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+asyncpg://", 1)
elif DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)

engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def create_tables():
    """Create all database tables on startup, then apply any pending column migrations."""
    from app import models  # noqa: F401 — import so models register with Base
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        # Widen recipient column from varchar(512) → text so long recipient lists don't crash sync
        try:
            await conn.execute(text(
                "ALTER TABLE emails ALTER COLUMN recipient TYPE TEXT"
            ))
        except Exception:
            pass  # Column already TEXT or table doesn't exist yet — safe to ignore


async def get_db():
    """FastAPI dependency that yields a database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
