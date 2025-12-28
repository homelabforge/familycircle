"""Authentication service - user accounts, sessions, and family management."""

import random
import secrets
import string
from datetime import datetime, timedelta, timezone
from typing import Optional

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import (
    User,
    Family,
    FamilyMembership,
    FamilyRole,
    UserProfile,
    ProfileVisibility,
    Setting,
)

ph = PasswordHasher()


def generate_family_code() -> str:
    """Generate a unique family code."""
    letters = "".join(random.choices(string.ascii_uppercase, k=6))
    numbers = str(random.randint(10, 99))
    return f"{letters}-{numbers}"


# ============ Settings ============


async def get_setting(
    session: AsyncSession, key: str, family_id: Optional[str] = None
) -> Optional[str]:
    """Get a setting value (global or per-family)."""
    result = await session.execute(
        select(Setting).where(Setting.key == key, Setting.family_id == family_id)
    )
    setting = result.scalar_one_or_none()
    return setting.value if setting else None


async def set_setting(
    session: AsyncSession, key: str, value: str, family_id: Optional[str] = None
) -> None:
    """Set a setting value (global or per-family)."""
    result = await session.execute(
        select(Setting).where(Setting.key == key, Setting.family_id == family_id)
    )
    setting = result.scalar_one_or_none()
    if setting:
        setting.value = value
    else:
        session.add(Setting(key=key, value=value, family_id=family_id))
    await session.commit()


# ============ User Lookups ============


async def get_user_by_email(session: AsyncSession, email: str) -> Optional[User]:
    """Get user by email."""
    result = await session.execute(
        select(User)
        .options(selectinload(User.family_memberships).selectinload(FamilyMembership.family))
        .where(User.email == email.lower())
    )
    return result.scalar_one_or_none()


async def get_user_by_id(session: AsyncSession, user_id: str) -> Optional[User]:
    """Get user by ID."""
    result = await session.execute(
        select(User)
        .options(selectinload(User.family_memberships).selectinload(FamilyMembership.family))
        .where(User.id == user_id)
    )
    return result.scalar_one_or_none()


async def get_user_by_session(session: AsyncSession, token: str) -> Optional[User]:
    """Get user by session token."""
    result = await session.execute(
        select(User)
        .options(selectinload(User.family_memberships).selectinload(FamilyMembership.family))
        .where(
            User.session_token == token,
            User.session_expires > datetime.now(timezone.utc),
        )
    )
    return result.scalar_one_or_none()


async def get_user_by_magic_token(session: AsyncSession, token: str) -> Optional[User]:
    """Get user by magic link token (for password recovery)."""
    result = await session.execute(
        select(User)
        .options(selectinload(User.family_memberships).selectinload(FamilyMembership.family))
        .where(
            User.magic_token == token,
            User.magic_token_expires > datetime.now(timezone.utc),
        )
    )
    return result.scalar_one_or_none()


# ============ Family Lookups ============


async def get_family_by_code(session: AsyncSession, code: str) -> Optional[Family]:
    """Get family by its join code."""
    result = await session.execute(
        select(Family).where(Family.family_code == code.upper())
    )
    return result.scalar_one_or_none()


async def get_family_by_id(session: AsyncSession, family_id: str) -> Optional[Family]:
    """Get family by ID."""
    result = await session.execute(select(Family).where(Family.id == family_id))
    return result.scalar_one_or_none()


async def get_user_membership(
    session: AsyncSession, user_id: str, family_id: str
) -> Optional[FamilyMembership]:
    """Get user's membership in a specific family."""
    result = await session.execute(
        select(FamilyMembership)
        .options(selectinload(FamilyMembership.family))
        .where(
            FamilyMembership.user_id == user_id,
            FamilyMembership.family_id == family_id,
        )
    )
    return result.scalar_one_or_none()


# ============ Session Management ============


async def create_session(user: User, session: AsyncSession) -> str:
    """Create a new session for a user."""
    user.session_token = secrets.token_urlsafe(32)
    user.session_expires = datetime.now(timezone.utc) + timedelta(days=30)
    await session.commit()
    return user.session_token


async def logout(session: AsyncSession, user: User) -> None:
    """Clear user session."""
    user.session_token = None
    user.session_expires = None
    await session.commit()


# ============ Password Management ============


async def verify_password(
    session: AsyncSession, email: str, password: str
) -> Optional[User]:
    """Verify email + password login."""
    user = await get_user_by_email(session, email)
    if not user or not user.password_hash:
        return None

    try:
        ph.verify(user.password_hash, password)
        # Create session on successful login
        await create_session(user, session)
        return user
    except VerifyMismatchError:
        return None


async def set_password(session: AsyncSession, user: User, password: str) -> None:
    """Set password for a user."""
    user.password_hash = ph.hash(password)
    await session.commit()


async def change_password(
    session: AsyncSession, user: User, current_password: str, new_password: str
) -> bool:
    """Change password (requires current password)."""
    if not user.password_hash:
        return False

    try:
        ph.verify(user.password_hash, current_password)
        user.password_hash = ph.hash(new_password)
        await session.commit()
        return True
    except VerifyMismatchError:
        return False


# ============ Magic Link (Password Recovery) ============


async def create_magic_link(session: AsyncSession, email: str) -> Optional[str]:
    """Create a magic link token for password recovery."""
    user = await get_user_by_email(session, email)
    if not user:
        return None

    # Get expiry days from settings
    expiry_days = int(await get_setting(session, "magic_link_expiry_days") or "1")

    # Generate token
    token = secrets.token_urlsafe(32)
    user.magic_token = token
    user.magic_token_expires = datetime.now(timezone.utc) + timedelta(days=expiry_days)

    await session.commit()
    return token


async def verify_magic_token_and_reset_password(
    session: AsyncSession, token: str, new_password: str
) -> Optional[User]:
    """Verify magic token and reset password."""
    user = await get_user_by_magic_token(session, token)
    if not user:
        return None

    # Clear magic token (one-time use)
    user.magic_token = None
    user.magic_token_expires = None

    # Set new password
    user.password_hash = ph.hash(new_password)

    # Create session for immediate login
    user.session_token = secrets.token_urlsafe(32)
    user.session_expires = datetime.now(timezone.utc) + timedelta(days=30)

    await session.commit()
    return user


# ============ User & Family Creation ============


async def create_user(
    session: AsyncSession,
    email: str,
    password: str,
    is_super_admin: bool = False,
) -> User:
    """Create a new user account."""
    user = User(
        email=email.lower(),
        password_hash=ph.hash(password),
        is_super_admin=is_super_admin,
    )
    session.add(user)
    # Flush to generate UUID for user.id
    await session.flush()

    # Create empty profile
    profile = UserProfile(user_id=str(user.id))
    session.add(profile)

    await session.commit()
    await session.refresh(user)
    return user


async def create_family(session: AsyncSession, name: str) -> Family:
    """Create a new family with a unique code."""
    # Generate unique code
    code = generate_family_code()
    while await get_family_by_code(session, code):
        code = generate_family_code()

    family = Family(name=name, family_code=code)
    session.add(family)
    await session.commit()
    await session.refresh(family)
    return family


async def add_user_to_family(
    session: AsyncSession,
    user: User,
    family: Family,
    display_name: str,
    role: FamilyRole = FamilyRole.MEMBER,
) -> FamilyMembership:
    """Add a user to a family."""
    membership = FamilyMembership(
        user_id=str(user.id),
        family_id=str(family.id),
        display_name=display_name,
        role=role,
    )
    session.add(membership)

    # Create default visibility settings (show everything)
    visibility = ProfileVisibility(
        user_id=str(user.id),
        family_id=str(family.id),
        show_email=True,
        show_phone=True,
        show_address=True,
    )
    session.add(visibility)

    await session.commit()
    await session.refresh(membership)
    return membership


async def register_with_family_code(
    session: AsyncSession,
    family_code: str,
    email: str,
    password: str,
    display_name: str,
) -> tuple[Optional[User], Optional[str]]:
    """
    Register a new user or add existing user to a family.
    Returns (user, error_message).
    """
    # Find family by code
    family = await get_family_by_code(session, family_code)
    if not family:
        return None, "Invalid family code"

    # Check if email already exists
    existing_user = await get_user_by_email(session, email)

    if existing_user:
        # Check if already in this family
        membership = await get_user_membership(session, existing_user.id, family.id)
        if membership:
            return None, "You are already a member of this family. Please log in."

        # Add existing user to family
        await add_user_to_family(session, existing_user, family, display_name)
        existing_user.current_family_id = family.id
        await create_session(existing_user, session)
        # Expire and re-fetch user with all relationships loaded
        user_id = str(existing_user.id)
        session.expire(existing_user)
        user = await get_user_by_id(session, user_id)
        return user, None
    else:
        # Create new user
        user = await create_user(session, email, password)
        await add_user_to_family(session, user, family, display_name)
        user.current_family_id = family.id
        await create_session(user, session)
        # Expire and re-fetch user with all relationships loaded
        user_id = str(user.id)
        session.expire(user)
        user = await get_user_by_id(session, user_id)
        return user, None


# ============ Family Context Switching ============


async def switch_family(
    session: AsyncSession, user: User, family_id: str
) -> Optional[FamilyMembership]:
    """Switch user's active family context."""
    membership = await get_user_membership(session, user.id, family_id)
    if not membership:
        return None

    user.current_family_id = family_id
    await session.commit()
    return membership


# ============ Setup ============


async def check_needs_setup(session: AsyncSession) -> bool:
    """Check if initial setup is needed (no super admins exist)."""
    from sqlalchemy import func

    result = await session.execute(
        select(func.count()).select_from(User).where(User.is_super_admin == True)  # noqa: E712
    )
    return result.scalar() == 0


async def initial_setup(
    session: AsyncSession,
    email: str,
    password: str,
    display_name: str,
    family_name: str,
) -> tuple[User, Family]:
    """
    Initial platform setup - creates super admin and first family.
    Only works if no super admins exist.
    """
    if not await check_needs_setup(session):
        raise ValueError("Setup already complete")

    # Create super admin user
    user = await create_user(session, email, password, is_super_admin=True)

    # Create first family
    family = await create_family(session, family_name)

    # Add super admin to family as admin
    await add_user_to_family(session, user, family, display_name, FamilyRole.ADMIN)

    # Set current family
    user.current_family_id = family.id

    # Create session
    await create_session(user, session)

    # Expire user to clear cached relationships, then re-fetch with all relationships
    user_id = str(user.id)
    session.expire(user)
    user = await get_user_by_id(session, user_id)

    return user, family


# ============ Helpers for API responses ============


def get_user_families_info(user: User) -> list[dict]:
    """Get list of families for a user with their role."""
    families = []
    for membership in user.family_memberships:
        families.append({
            "id": membership.family.id,
            "name": membership.family.name,
            "family_code": membership.family.family_code,
            "role": membership.role.value,
        })
    return families


def get_current_family_context(user: User) -> dict:
    """Get user's current family context info."""
    if not user.current_family_id:
        return {
            "current_family_id": None,
            "current_family_name": None,
            "display_name": None,
            "role_in_family": None,
        }

    for membership in user.family_memberships:
        if membership.family_id == user.current_family_id:
            return {
                "current_family_id": membership.family_id,
                "current_family_name": membership.family.name,
                "display_name": membership.display_name,
                "role_in_family": membership.role.value,
            }

    return {
        "current_family_id": user.current_family_id,
        "current_family_name": None,
        "display_name": None,
        "role_in_family": None,
    }
