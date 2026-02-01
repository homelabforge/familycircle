"""Settings API endpoints - multi-family aware.

Settings are scoped:
- Global settings (family_id=NULL): secret_key, app_name, smtp_*, etc.
- Family settings (family_id set): theme_color, etc.

User preferences are stored on the User model.
"""

import random
import string

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth import get_current_user, get_optional_user, require_family_context
from app.db import get_db_session
from app.models import Family, Setting, User
from app.services.permissions import permissions

router = APIRouter()


async def get_global_setting(db: AsyncSession, key: str) -> str | None:
    """Get a global setting value (family_id is NULL)."""
    result = await db.execute(
        select(Setting).where(Setting.key == key, Setting.family_id.is_(None))
    )
    setting = result.scalar_one_or_none()
    return setting.value if setting else None


async def set_global_setting(db: AsyncSession, key: str, value: str) -> None:
    """Set a global setting value."""
    result = await db.execute(
        select(Setting).where(Setting.key == key, Setting.family_id.is_(None))
    )
    setting = result.scalar_one_or_none()
    if setting:
        setting.value = value
    else:
        db.add(Setting(key=key, value=value, family_id=None))
    await db.commit()


async def get_family_setting(db: AsyncSession, family_id: str, key: str) -> str | None:
    """Get a family-specific setting value."""
    result = await db.execute(
        select(Setting).where(Setting.key == key, Setting.family_id == family_id)
    )
    setting = result.scalar_one_or_none()
    return setting.value if setting else None


async def set_family_setting(db: AsyncSession, family_id: str, key: str, value: str) -> None:
    """Set a family-specific setting value."""
    result = await db.execute(
        select(Setting).where(Setting.key == key, Setting.family_id == family_id)
    )
    setting = result.scalar_one_or_none()
    if setting:
        setting.value = value
    else:
        db.add(Setting(key=key, value=value, family_id=family_id))
    await db.commit()


@router.get("")
async def get_settings(
    user: User | None = Depends(get_optional_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Get application settings.

    - Public: app_name
    - Authenticated: family-specific settings
    - Super admin: SMTP and other sensitive global settings
    """
    # Public settings available to all
    public_settings = {
        "app_name": await get_global_setting(db, "app_name") or "FamilyCircle",
    }

    if not user:
        return {"settings": public_settings}

    # Get family settings if user has a current family
    family_settings = {}
    if user.current_family_id:
        family_settings = {
            "theme_color": (
                await get_family_setting(db, user.current_family_id, "theme_color") or "teal"
            ),
        }

    # Check if super admin for sensitive settings
    is_super = permissions.is_super_admin(user)
    if is_super:
        smtp_password = await get_global_setting(db, "smtp_password")
        admin_settings = {
            "magic_link_expiry_days": await get_global_setting(db, "magic_link_expiry_days")
            or "90",
            "cancelled_event_retention_days": await get_global_setting(
                db, "cancelled_event_retention_days"
            )
            or "7",
            # SMTP settings (password masked)
            "smtp_host": await get_global_setting(db, "smtp_host") or "",
            "smtp_port": await get_global_setting(db, "smtp_port") or "587",
            "smtp_username": await get_global_setting(db, "smtp_username") or "",
            "smtp_password": "********" if smtp_password else "",
            "smtp_from_email": await get_global_setting(db, "smtp_from_email") or "",
            "smtp_from_name": await get_global_setting(db, "smtp_from_name") or "",
            "smtp_use_tls": await get_global_setting(db, "smtp_use_tls") or "true",
            "smtp_configured": bool(await get_global_setting(db, "smtp_host") and smtp_password),
        }
        return {
            "settings": {
                **public_settings,
                **family_settings,
                **admin_settings,
            }
        }

    return {"settings": {**public_settings, **family_settings}}


class UpdateGlobalSettingsRequest(BaseModel):
    """Update global settings request (super admin only)."""

    app_name: str | None = None
    magic_link_expiry_days: str | None = None
    cancelled_event_retention_days: str | None = None
    # SMTP settings
    smtp_host: str | None = None
    smtp_port: str | None = None
    smtp_username: str | None = None
    smtp_password: str | None = None
    smtp_from_email: str | None = None
    smtp_from_name: str | None = None
    smtp_use_tls: str | None = None  # "true" or "false"


@router.put("/global")
async def update_global_settings(
    request: UpdateGlobalSettingsRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Update global application settings (super admin only)."""
    if not permissions.is_super_admin(user):
        raise HTTPException(status_code=403, detail="Only super admins can change global settings")

    if request.app_name:
        await set_global_setting(db, "app_name", request.app_name)
    if request.magic_link_expiry_days:
        await set_global_setting(db, "magic_link_expiry_days", request.magic_link_expiry_days)
    if request.cancelled_event_retention_days:
        await set_global_setting(
            db, "cancelled_event_retention_days", request.cancelled_event_retention_days
        )

    # SMTP settings
    if request.smtp_host is not None:
        await set_global_setting(db, "smtp_host", request.smtp_host)
    if request.smtp_port is not None:
        await set_global_setting(db, "smtp_port", request.smtp_port)
    if request.smtp_username is not None:
        await set_global_setting(db, "smtp_username", request.smtp_username)
    # Only update password if not masked value
    if request.smtp_password is not None and request.smtp_password != "********":
        await set_global_setting(db, "smtp_password", request.smtp_password)
    if request.smtp_from_email is not None:
        await set_global_setting(db, "smtp_from_email", request.smtp_from_email)
    if request.smtp_from_name is not None:
        await set_global_setting(db, "smtp_from_name", request.smtp_from_name)
    if request.smtp_use_tls is not None:
        await set_global_setting(db, "smtp_use_tls", request.smtp_use_tls)

    return {"message": "Global settings updated"}


class UpdateFamilySettingsRequest(BaseModel):
    """Update family settings request."""

    theme_color: str | None = None


@router.put("/family")
async def update_family_settings(
    request: UpdateFamilySettingsRequest,
    user: User = Depends(require_family_context),
    db: AsyncSession = Depends(get_db_session),
):
    """Update family-specific settings (family admin only)."""
    is_admin = await permissions.is_family_admin(db, user, user.current_family_id)
    if not is_admin:
        raise HTTPException(status_code=403, detail="Only family admins can change family settings")

    if request.theme_color:
        await set_family_setting(db, user.current_family_id, "theme_color", request.theme_color)

    return {"message": "Family settings updated"}


@router.get("/family-code")
async def get_family_code(
    user: User = Depends(require_family_context),
    db: AsyncSession = Depends(get_db_session),
):
    """Get the current family's join code (family admin only)."""
    is_admin = await permissions.is_family_admin(db, user, user.current_family_id)
    if not is_admin:
        raise HTTPException(status_code=403, detail="Only family admins can view the family code")

    result = await db.execute(select(Family).where(Family.id == user.current_family_id))
    family = result.scalar_one_or_none()
    if not family:
        raise HTTPException(status_code=404, detail="Family not found")

    return {"code": family.family_code, "family_name": family.name}


@router.post("/family-code/regenerate")
async def regenerate_family_code(
    user: User = Depends(require_family_context),
    db: AsyncSession = Depends(get_db_session),
):
    """Regenerate the family join code (family admin only)."""
    is_admin = await permissions.is_family_admin(db, user, user.current_family_id)
    if not is_admin:
        raise HTTPException(
            status_code=403, detail="Only family admins can regenerate the family code"
        )

    result = await db.execute(select(Family).where(Family.id == user.current_family_id))
    family = result.scalar_one_or_none()
    if not family:
        raise HTTPException(status_code=404, detail="Family not found")

    # Generate new code
    new_code = (
        "".join(random.choices(string.ascii_uppercase, k=6)) + "-" + str(random.randint(10, 99))
    )
    family.family_code = new_code
    await db.commit()

    return {"code": new_code}


@router.get("/user-preferences")
async def get_user_preferences(user: User = Depends(get_current_user)):
    """Get current user's preferences."""
    return {
        "theme": user.theme,
        "big_mode": user.big_mode,
    }


class UserPreferencesRequest(BaseModel):
    """User preferences update."""

    theme: str | None = None
    big_mode: bool | None = None


@router.put("/user-preferences")
async def update_user_preferences(
    request: UserPreferencesRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Update current user's preferences."""
    if request.theme is not None:
        if request.theme not in ("light", "dark", "system"):
            raise HTTPException(
                status_code=400, detail="Theme must be 'light', 'dark', or 'system'"
            )
        user.theme = request.theme

    if request.big_mode is not None:
        user.big_mode = request.big_mode

    await db.commit()

    return {
        "message": "Preferences updated",
        "theme": user.theme,
        "big_mode": user.big_mode,
    }


# Backwards compatibility - redirect old PUT to global settings
@router.put("")
async def update_settings_compat(
    request: UpdateGlobalSettingsRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Update settings (backwards compatibility, redirects to global)."""
    return await update_global_settings(request, user, db)
