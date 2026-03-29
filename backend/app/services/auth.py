"""Authentication service - user accounts, sessions, and family management."""

import random
import secrets
import string
from datetime import UTC, datetime, timedelta

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.constants import SESSION_TOKEN_EXPIRY_DAYS
from app.models import (
    Family,
    FamilyMembership,
    FamilyRole,
    ProfileVisibility,
    Setting,
    User,
    UserProfile,
)
from app.models.token import Token, TokenType

ph = PasswordHasher()


def generate_family_code() -> str:
    """Generate a unique family code."""
    letters = "".join(random.choices(string.ascii_uppercase, k=6))
    numbers = str(random.randint(10, 99))
    return f"{letters}-{numbers}"


# ============ Settings ============


async def get_setting(session: AsyncSession, key: str, family_id: str | None = None) -> str | None:
    """Get a setting value (global or per-family)."""
    result = await session.execute(
        select(Setting).where(Setting.key == key, Setting.family_id == family_id)
    )
    setting = result.scalar_one_or_none()
    return setting.value if setting else None


async def set_setting(
    session: AsyncSession, key: str, value: str, family_id: str | None = None
) -> None:
    """Set a setting value (global or per-family).

    Does not commit — caller or request-level session manager handles commit.
    """
    result = await session.execute(
        select(Setting).where(Setting.key == key, Setting.family_id == family_id)
    )
    setting = result.scalar_one_or_none()
    if setting:
        setting.value = value
    else:
        session.add(Setting(key=key, value=value, family_id=family_id))


# ============ Eager-loading helper ============

_FAMILY_EAGER_LOAD = selectinload(User.family_memberships).selectinload(FamilyMembership.family)
"""Caller contract: use this when the returned User will be passed to
build_user_response(), get_current_family_context(), or get_user_families_info()
— i.e., any code that walks user.family_memberships[].family.
Identity-only and permission-only flows must NOT use this."""


# ============ User Lookups — Lightweight (no eager loading) ============


async def get_user_by_session(session: AsyncSession, token: str) -> User | None:
    """Get user by session token (lightweight — no family eager loading).

    Used by get_current_user dependency for most API endpoints.
    Reads from Token table only (legacy User column fallback removed — M2).
    """
    now = datetime.now(UTC)

    token_result = await session.execute(
        select(Token).where(
            Token.token == token,
            Token.token_type == TokenType.SESSION,
            Token.expires_at > now,
        )
    )
    token_row = token_result.scalar_one_or_none()
    if not token_row:
        return None

    result = await session.execute(select(User).where(User.id == token_row.user_id))
    return result.scalar_one_or_none()


async def get_user_by_id(session: AsyncSession, user_id: str) -> User | None:
    """Get user by ID (lightweight — no family eager loading)."""
    result = await session.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def get_user_by_email(session: AsyncSession, email: str) -> User | None:
    """Get user by email (lightweight — no family eager loading)."""
    result = await session.execute(select(User).where(User.email == email.lower()))
    return result.scalar_one_or_none()


# ============ User Lookups — Family-loaded (for build_user_response callers) ============


async def get_user_by_id_with_families(session: AsyncSession, user_id: str) -> User | None:
    """Get user by ID with family memberships eager-loaded.

    Use when the returned User will be passed to build_user_response().
    """
    result = await session.execute(
        select(User).options(_FAMILY_EAGER_LOAD).where(User.id == user_id)
    )
    return result.scalar_one_or_none()


async def get_user_by_email_with_families(session: AsyncSession, email: str) -> User | None:
    """Get user by email with family memberships eager-loaded.

    Use when the returned User will be passed to build_user_response().
    """
    result = await session.execute(
        select(User).options(_FAMILY_EAGER_LOAD).where(User.email == email.lower())
    )
    return result.scalar_one_or_none()


async def get_user_by_magic_token(session: AsyncSession, token: str) -> User | None:
    """Get user by magic link token (for password recovery).

    Returns family-loaded user (needed for build_user_response after password reset).
    Reads from Token table only (legacy User column fallback removed — M2).
    """
    now = datetime.now(UTC)

    token_result = await session.execute(
        select(Token).where(
            Token.token == token,
            Token.token_type == TokenType.MAGIC_LINK,
            Token.expires_at > now,
        )
    )
    token_row = token_result.scalar_one_or_none()
    if not token_row:
        return None

    result = await session.execute(
        select(User).options(_FAMILY_EAGER_LOAD).where(User.id == token_row.user_id)
    )
    return result.scalar_one_or_none()


# ============ Family Lookups ============


async def get_family_by_code(session: AsyncSession, code: str) -> Family | None:
    """Get family by its join code."""
    result = await session.execute(select(Family).where(Family.family_code == code.upper()))
    return result.scalar_one_or_none()


async def get_family_by_id(session: AsyncSession, family_id: str) -> Family | None:
    """Get family by ID."""
    result = await session.execute(select(Family).where(Family.id == family_id))
    return result.scalar_one_or_none()


async def get_users_with_single_membership(session: AsyncSession, family_id: str) -> list[str]:
    """Return emails of users whose ONLY family membership is in the given family.

    Two-step query: find users with exactly one membership globally,
    then intersect with users who are members of the target family.
    """
    # Subquery: user_ids with exactly one membership across all families
    single_membership_subq = (
        select(FamilyMembership.user_id)
        .group_by(FamilyMembership.user_id)
        .having(func.count() == 1)
        .subquery()
    )

    # Users in the target family who appear in the single-membership set
    stmt = (
        select(User.email)
        .join(FamilyMembership, User.id == FamilyMembership.user_id)
        .where(
            FamilyMembership.family_id == family_id,
            FamilyMembership.user_id.in_(select(single_membership_subq.c.user_id)),
        )
    )
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def delete_family(session: AsyncSession, family_id: str) -> tuple[str, list[str] | None]:
    """Delete a family by ID.

    Returns (family_name, orphaned_emails_or_none).
    - If orphaned users exist, returns (name, [emails]) without deleting.
    - If no orphans, deletes the family and returns (name, None).

    Raises ValueError if family not found.
    Does not commit — caller or request-level session manager handles commit.
    """
    family = await get_family_by_id(session, family_id)
    if not family:
        raise ValueError("Family not found")

    # Check for users who would be orphaned
    orphaned_emails = await get_users_with_single_membership(session, family_id)
    if orphaned_emails:
        return family.name, orphaned_emails

    # Auto-switch users whose active family is being deleted to their
    # first remaining family (avoids leaving them in a null-context limbo
    # where the UI has no family selector visible).
    affected_users_result = await session.execute(
        select(User).where(User.current_family_id == family_id)
    )
    for user in affected_users_result.scalars().all():
        # Find their first membership that ISN'T in the family being deleted
        alt_result = await session.execute(
            select(FamilyMembership.family_id)
            .where(
                FamilyMembership.user_id == user.id,
                FamilyMembership.family_id != family_id,
            )
            .limit(1)
        )
        alt_family_id = alt_result.scalar_one_or_none()
        user.current_family_id = (
            alt_family_id  # None if no other families (shouldn't happen — orphan guard)
        )

    # Safe to delete — cascades handle memberships, events, visibility
    await session.delete(family)
    await session.flush()
    return family.name, None


async def get_user_membership(
    session: AsyncSession, user_id: str, family_id: str
) -> FamilyMembership | None:
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
    """Create a new session for a user.

    Writes to Token table only (legacy User column dual-write removed — M2).
    Multi-session: does NOT invalidate existing sessions.

    Does not commit — caller or request-level session manager handles commit.
    """
    token_value = secrets.token_urlsafe(32)
    expires = datetime.now(UTC) + timedelta(days=SESSION_TOKEN_EXPIRY_DAYS)

    session.add(
        Token(
            user_id=str(user.id),
            token=token_value,
            token_type=TokenType.SESSION,
            expires_at=expires,
        )
    )

    await session.flush()
    return token_value


async def logout(session: AsyncSession, token: str) -> None:
    """Clear a specific session by its token value.

    Multi-session: deletes only the specified session token row.
    Other sessions (other devices) stay active.

    Does not commit — caller or request-level session manager handles commit.
    """
    await session.execute(
        delete(Token).where(
            Token.token == token,
            Token.token_type == TokenType.SESSION,
        )
    )


# ============ Password Management ============


async def verify_password(
    session: AsyncSession, email: str, password: str
) -> tuple[User | None, str | None]:
    """Verify email + password login.

    Returns (user, session_token) or (None, None).
    Uses family-loaded lookup because login response needs build_user_response().
    """
    user = await get_user_by_email_with_families(session, email)
    if not user or not user.password_hash:
        return None, None

    try:
        ph.verify(user.password_hash, password)
        # Create session on successful login
        session_token = await create_session(user, session)
        return user, session_token
    except VerifyMismatchError:
        return None, None


async def set_password(session: AsyncSession, user: User, password: str) -> None:
    """Set password for a user.

    Does not commit — caller or request-level session manager handles commit.
    """
    user.password_hash = ph.hash(password)


async def change_password(
    session: AsyncSession, user: User, current_password: str, new_password: str
) -> bool:
    """Change password (requires current password)."""
    if not user.password_hash:
        return False

    try:
        ph.verify(user.password_hash, current_password)
        user.password_hash = ph.hash(new_password)
        return True
    except VerifyMismatchError:
        return False


# ============ Magic Link (Password Recovery) ============


async def create_magic_link(session: AsyncSession, email: str) -> str | None:
    """Create a magic link token for password recovery.

    One active magic_link per user — new request overwrites old.
    Writes to Token table only (legacy User column dual-write removed — M2).
    """
    user = await get_user_by_email(session, email)
    if not user:
        return None

    # Get expiry days from settings
    expiry_days = int(await get_setting(session, "magic_link_expiry_days") or "1")

    # Generate token
    token_value = secrets.token_urlsafe(32)
    expires = datetime.now(UTC) + timedelta(days=expiry_days)

    # Token table — delete old magic_link, create new
    await session.execute(
        delete(Token).where(
            Token.user_id == user.id,
            Token.token_type == TokenType.MAGIC_LINK,
        )
    )
    session.add(
        Token(
            user_id=str(user.id),
            token=token_value,
            token_type=TokenType.MAGIC_LINK,
            expires_at=expires,
        )
    )

    await session.flush()
    return token_value


async def verify_magic_token_and_reset_password(
    session: AsyncSession, token: str, new_password: str
) -> tuple[User | None, str | None]:
    """Verify magic token and reset password.

    Security: invalidates ALL tokens for the user (compromised password means
    all sessions are suspect), then creates one new session token.

    Returns (user, session_token) or (None, None).
    """
    user = await get_user_by_magic_token(session, token)
    if not user:
        return None, None

    # Delete ALL tokens for this user (sessions + magic links)
    await session.execute(delete(Token).where(Token.user_id == user.id))

    # Set new password
    user.password_hash = ph.hash(new_password)

    # Create new session
    session_token = await create_session(user, session)

    return user, session_token


# ============ User & Family Creation ============


async def create_user(
    session: AsyncSession,
    email: str,
    password: str,
    is_super_admin: bool = False,
) -> User:
    """Create a new user account.

    Does not commit — caller or request-level session manager handles commit.
    Flushes to generate the user ID needed for the profile.
    """
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

    await session.flush()
    return user


async def create_family(session: AsyncSession, name: str) -> Family:
    """Create a new family with a unique code.

    Does not commit — caller or request-level session manager handles commit.
    Flushes to generate the family ID.
    """
    # Generate unique code
    code = generate_family_code()
    while await get_family_by_code(session, code):
        code = generate_family_code()

    family = Family(name=name, family_code=code)
    session.add(family)
    await session.flush()
    return family


async def add_user_to_family(
    session: AsyncSession,
    user: User,
    family: Family,
    display_name: str,
    role: FamilyRole = FamilyRole.MEMBER,
) -> FamilyMembership:
    """Add a user to a family.

    Does not commit — caller or request-level session manager handles commit.
    Flushes to generate the membership ID.
    """
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

    await session.flush()
    return membership


async def register_with_family_code(
    session: AsyncSession,
    family_code: str,
    email: str,
    password: str,
    display_name: str,
) -> tuple[User | None, str | None, str | None]:
    """Register a new user or add existing user to a family.

    Returns (user, error_message, session_token).
    On success: (user, None, token). On error: (None, error_msg, None).
    """
    # Find family by code
    family = await get_family_by_code(session, family_code)
    if not family:
        return None, "Invalid family code", None

    # Check if email already exists
    existing_user = await get_user_by_email(session, email)

    if existing_user:
        # Check if already in this family
        membership = await get_user_membership(session, existing_user.id, family.id)
        if membership:
            return None, "You are already a member of this family. Please log in.", None

        # Add existing user to family
        await add_user_to_family(session, existing_user, family, display_name)
        existing_user.current_family_id = family.id
        token = await create_session(existing_user, session)
        # Expire and re-fetch user with all relationships loaded
        user_id = str(existing_user.id)
        session.expire(existing_user)
        user = await get_user_by_id_with_families(session, user_id)
        return user, None, token
    else:
        # Create new user
        user = await create_user(session, email, password)
        await add_user_to_family(session, user, family, display_name)
        user.current_family_id = family.id
        token = await create_session(user, session)
        # Expire and re-fetch user with all relationships loaded
        user_id = str(user.id)
        session.expire(user)
        user = await get_user_by_id_with_families(session, user_id)
        return user, None, token


# ============ Family Context Switching ============


async def switch_family(
    session: AsyncSession, user: User, family_id: str
) -> FamilyMembership | None:
    """Switch user's active family context.

    Does not commit — caller or request-level session manager handles commit.
    """
    membership = await get_user_membership(session, user.id, family_id)
    if not membership:
        return None

    user.current_family_id = family_id
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
) -> tuple[User, Family, str]:
    """Initial platform setup - creates super admin and first family.

    Only works if no super admins exist.
    Returns (user, family, session_token).
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
    session_token = await create_session(user, session)

    # Expire user to clear cached relationships, then re-fetch with all relationships
    user_id = str(user.id)
    session.expire(user)
    refreshed = await get_user_by_id_with_families(session, user_id)
    if not refreshed:
        raise RuntimeError(f"User {user_id} disappeared after setup")

    return refreshed, family, session_token


# ============ Helpers for API responses ============


def get_user_families_info(user: User) -> list[dict]:
    """Get list of families for a user with their role."""
    families = []
    for membership in user.family_memberships:
        families.append(
            {
                "id": membership.family.id,
                "name": membership.family.name,
                "family_code": membership.family.family_code,
                "role": membership.role.value,
            }
        )
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
