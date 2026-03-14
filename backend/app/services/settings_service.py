"""Typed settings service — replaces raw key-value lookups with Pydantic models.

Provides typed access to global settings stored in the Setting table.
Replaces ad-hoc _get_setting() calls scattered across services.
"""

from __future__ import annotations

from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Setting


class SmtpConfig(BaseModel):
    """SMTP email configuration."""

    host: str = ""
    port: int = 587
    username: str = ""
    password: str = ""
    from_email: str = ""
    from_name: str = "FamilyCircle"
    use_tls: bool = True

    @property
    def is_configured(self) -> bool:
        """Check if SMTP is fully configured."""
        return bool(self.host and self.password and self.from_email)


class NotificationRetryConfig(BaseModel):
    """Notification retry settings."""

    retry_attempts: int = 3
    retry_delay: float = 2.0


class AppConfig(BaseModel):
    """Application-level settings."""

    app_name: str = "FamilyCircle"
    secret_key: str = ""
    magic_link_expiry_days: int = 1


async def _get_global(db: AsyncSession, key: str) -> str | None:
    """Read a single global setting value (family_id is NULL)."""
    result = await db.execute(
        select(Setting).where(Setting.key == key, Setting.family_id.is_(None))
    )
    setting = result.scalar_one_or_none()
    return setting.value if setting else None


async def _get_global_or(db: AsyncSession, key: str, default: str) -> str:
    """Read a global setting, returning default if missing."""
    return await _get_global(db, key) or default


async def _get_global_bool(db: AsyncSession, key: str, default: bool = False) -> bool:
    """Read a global boolean setting."""
    value = await _get_global_or(db, key, str(default).lower())
    return value.lower() in ("true", "1", "yes")


async def _get_global_int(db: AsyncSession, key: str, default: int = 0) -> int:
    """Read a global integer setting."""
    try:
        return int(await _get_global_or(db, key, str(default)))
    except ValueError:
        return default


class SettingsService:
    """Typed access to global settings."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_smtp_config(self) -> SmtpConfig:
        """Load SMTP configuration from settings."""
        return SmtpConfig(
            host=await _get_global_or(self.db, "smtp_host", ""),
            port=await _get_global_int(self.db, "smtp_port", 587),
            username=await _get_global_or(self.db, "smtp_username", ""),
            password=await _get_global_or(self.db, "smtp_password", ""),
            from_email=await _get_global_or(self.db, "smtp_from_email", ""),
            from_name=await _get_global_or(self.db, "smtp_from_name", "FamilyCircle"),
            use_tls=await _get_global_bool(self.db, "smtp_use_tls", True),
        )

    async def get_notification_retry_config(self) -> NotificationRetryConfig:
        """Load notification retry settings."""
        return NotificationRetryConfig(
            retry_attempts=await _get_global_int(self.db, "notification_retry_attempts", 3),
            retry_delay=float(await _get_global_or(self.db, "notification_retry_delay", "2.0")),
        )

    async def get_app_config(self) -> AppConfig:
        """Load application-level settings."""
        return AppConfig(
            app_name=await _get_global_or(self.db, "app_name", "FamilyCircle"),
            secret_key=await _get_global_or(self.db, "secret_key", ""),
            magic_link_expiry_days=await _get_global_int(self.db, "magic_link_expiry_days", 1),
        )

    # Convenience: individual setting accessors for dispatcher's internal use
    async def get_setting(self, key: str, default: str = "") -> str:
        """Get a single global setting value."""
        return await _get_global_or(self.db, key, default)

    async def get_setting_bool(self, key: str, default: bool = False) -> bool:
        """Get a boolean global setting."""
        return await _get_global_bool(self.db, key, default)

    async def get_setting_int(self, key: str, default: int = 0) -> int:
        """Get an integer global setting."""
        return await _get_global_int(self.db, key, default)
