"""SQLAlchemy async database setup.

Supports SQLite (local dev) and PostgreSQL (Vercel / cloud).
Set DATABASE_URL to a postgres:// or postgresql:// URL for production.
"""

from __future__ import annotations

from sqlalchemy import Column, DateTime, Float, Integer, String, Text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from ..api.config import settings


def _normalize_db_url(url: str) -> str:
    """Normalize Vercel Postgres URL to an asyncpg-compatible form."""
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql+asyncpg://", 1)
    if url.startswith("postgresql://") and "+asyncpg" not in url:
        return url.replace("postgresql://", "postgresql+asyncpg://", 1)
    return url


_db_url = _normalize_db_url(settings.database_url)
_is_postgres = _db_url.startswith("postgresql+asyncpg")

engine = create_async_engine(
    _db_url,
    echo=False,
    # Serverless-friendly pool settings for Postgres
    pool_size=1 if _is_postgres else 5,
    max_overflow=0 if _is_postgres else 10,
)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


class SnapshotORM(Base):
    __tablename__ = "snapshots"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(36), index=True, nullable=False)
    captured_at = Column(DateTime(timezone=True), nullable=False, index=True)
    activity_category = Column(String(32), nullable=False)
    focus_level = Column(Integer, nullable=False)
    confidence = Column(Float, nullable=False)
    notes = Column(Text, default="")


class EnergyLogORM(Base):
    __tablename__ = "energy_logs"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(36), index=True, nullable=False)
    measured_at = Column(DateTime(timezone=True), nullable=False, index=True)
    focus_score = Column(Float, nullable=False)
    fatigue_score = Column(Float, nullable=False)
    recommended_break = Column(Integer, default=0)  # SQLite boolean
    estimated_optimal_work_minutes = Column(Integer, default=25)


async def init_db() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_db() -> AsyncSession:  # type: ignore[misc]
    async with AsyncSessionLocal() as session:
        yield session
