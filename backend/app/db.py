"""Database initialization and connection management."""

import logging
import secrets
import traceback
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import DATABASE_PATH
from app.models import (  # noqa: F401
    BabyShowerDetail,
    BirthdayDetail,
    Event,
    EventComment,
    EventRSVP,
    Family,
    FamilyMembership,
    GiftExchangeAssignment,
    GiftExchangeExclusion,
    GiftExchangeMessage,
    HolidayDetail,
    Poll,
    PollOption,
    PollVote,
    PotluckItem,
    ProfileVisibility,
    Setting,
    Token,
    User,
    UserProfile,
    WeddingDetail,
    WeddingPartyMember,
    WishlistItem,
)
from app.models.base import Base

logger = logging.getLogger(__name__)

# Create async engine
engine = create_async_engine(
    f"sqlite+aiosqlite:///{DATABASE_PATH}",
    echo=False,
    connect_args={"check_same_thread": False},
)

# Session factory
async_session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def init_db() -> None:
    """Initialize database with required PRAGMA settings and create tables."""
    async with engine.begin() as conn:
        # Apply SQLite PRAGMA settings
        await conn.exec_driver_sql("PRAGMA journal_mode=WAL")
        await conn.exec_driver_sql("PRAGMA busy_timeout=5000")
        await conn.exec_driver_sql("PRAGMA foreign_keys=ON")
        await conn.exec_driver_sql("PRAGMA synchronous=NORMAL")

        # Create all tables
        await conn.run_sync(Base.metadata.create_all)

    # Initialize default settings if not exists
    await init_default_settings()

    # Run database migrations
    logger.info("Running database migrations...")
    try:
        database_url = f"sqlite:///{DATABASE_PATH}"
        from app.migrations.runner import run_migrations

        migrations_dir = Path(__file__).parent / "migrations"
        run_migrations(database_url, migrations_dir)
    except Exception as e:
        logger.error(f"Migration error: {e}")
        traceback.print_exc()
        # Don't fail startup - log error and continue


async def init_default_settings() -> None:
    """Initialize default global settings on first run."""
    async with async_session_maker() as session:
        from sqlalchemy import select

        # Check if secret_key exists (global setting, family_id=NULL)
        result = await session.execute(
            select(Setting).where(Setting.key == "secret_key", Setting.family_id.is_(None))
        )
        if not result.scalar_one_or_none():
            # Generate secret key (global)
            session.add(Setting(key="secret_key", value=secrets.token_hex(32), family_id=None))

            # Default global settings
            session.add(Setting(key="app_name", value="FamilyCircle", family_id=None))
            session.add(Setting(key="magic_link_expiry_days", value="90", family_id=None))

            await session.commit()


@asynccontextmanager
async def get_db() -> AsyncGenerator[AsyncSession]:
    """Get database session as async context manager."""
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def get_db_session() -> AsyncGenerator[AsyncSession]:
    """Dependency for FastAPI routes."""
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
