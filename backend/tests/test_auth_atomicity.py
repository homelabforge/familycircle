"""Tests verifying transaction atomicity of auth service flows.

H3 fix: auth helpers (create_user, create_family, add_user_to_family, create_session)
now flush-only. The session manager commits once at the end of a request. These tests
verify that partial failures don't leave orphaned records.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.family import Family
from app.models.family_membership import FamilyMembership
from app.models.profile_visibility import ProfileVisibility
from app.models.token import Token
from app.models.user import User
from app.models.user_profile import UserProfile
from app.services import auth as auth_service


class TestCreateUserFlushOnly:
    """Verify create_user does not commit — caller controls the transaction."""

    async def test_create_user_does_not_commit(self, db: AsyncSession):
        """User is visible in the session after create_user, but not yet committed."""
        user = await auth_service.create_user(db, "test@example.com", "password123")

        assert user.id is not None
        assert user.email == "test@example.com"

        # Profile should also exist (created in create_user)
        result = await db.execute(select(UserProfile).where(UserProfile.user_id == user.id))
        profile = result.scalar_one_or_none()
        assert profile is not None

    async def test_create_user_rollback_leaves_nothing(self, db: AsyncSession):
        """If we rollback after create_user, no user or profile persists."""
        user = await auth_service.create_user(db, "rollback@example.com", "password123")
        user_id = user.id

        await db.rollback()

        result = await db.execute(select(User).where(User.id == user_id))
        assert result.scalar_one_or_none() is None

        result = await db.execute(select(UserProfile).where(UserProfile.user_id == user_id))
        assert result.scalar_one_or_none() is None


class TestCreateFamilyFlushOnly:
    """Verify create_family does not commit."""

    async def test_create_family_does_not_commit(self, db: AsyncSession):
        family = await auth_service.create_family(db, "Test Family")

        assert family.id is not None
        assert family.name == "Test Family"
        assert family.family_code is not None

    async def test_create_family_rollback_leaves_nothing(self, db: AsyncSession):
        family = await auth_service.create_family(db, "Rollback Family")
        family_id = family.id

        await db.rollback()

        result = await db.execute(select(Family).where(Family.id == family_id))
        assert result.scalar_one_or_none() is None


class TestAddUserToFamilyFlushOnly:
    """Verify add_user_to_family does not commit."""

    async def test_add_user_to_family_rollback_leaves_nothing(self, db: AsyncSession):
        user = await auth_service.create_user(db, "member@example.com", "password123")
        family = await auth_service.create_family(db, "Family")
        membership = await auth_service.add_user_to_family(db, user, family, "Member")

        user_id = user.id
        family_id = family.id
        membership_id = membership.id

        await db.rollback()

        # Everything should be gone
        assert (
            await db.execute(select(User).where(User.id == user_id))
        ).scalar_one_or_none() is None
        assert (
            await db.execute(select(Family).where(Family.id == family_id))
        ).scalar_one_or_none() is None
        assert (
            await db.execute(select(FamilyMembership).where(FamilyMembership.id == membership_id))
        ).scalar_one_or_none() is None
        assert (
            await db.execute(
                select(ProfileVisibility).where(
                    ProfileVisibility.user_id == user_id,
                    ProfileVisibility.family_id == family_id,
                )
            )
        ).scalar_one_or_none() is None


class TestCreateSessionFlushOnly:
    """Verify create_session does not commit."""

    async def test_create_session_rollback_leaves_nothing(self, db: AsyncSession):
        user = await auth_service.create_user(db, "session@example.com", "password123")
        await db.commit()  # Commit user so it persists

        token_value = await auth_service.create_session(user, db)
        assert token_value is not None

        await db.rollback()

        # Token should not persist
        result = await db.execute(select(Token).where(Token.token == token_value))
        assert result.scalar_one_or_none() is None


class TestInitialSetupAtomicity:
    """Verify initial_setup is atomic — all-or-nothing."""

    async def test_setup_succeeds_end_to_end(self, db: AsyncSession):
        """Happy path: setup creates user, family, membership, session."""
        user, family, session_token = await auth_service.initial_setup(
            db, "admin@example.com", "password123", "Admin", "First Family"
        )
        await db.commit()

        assert user is not None
        assert family is not None
        assert session_token is not None
        assert user.is_super_admin is True
        assert user.current_family_id == family.id

        # Membership exists
        result = await db.execute(
            select(FamilyMembership).where(
                FamilyMembership.user_id == user.id,
                FamilyMembership.family_id == family.id,
            )
        )
        assert result.scalar_one_or_none() is not None

        # Token exists
        result = await db.execute(select(Token).where(Token.user_id == user.id))
        assert result.scalar_one_or_none() is not None

    async def test_setup_failure_mid_flow_leaves_nothing(self, db: AsyncSession):
        """If add_user_to_family fails, no user or family should persist."""
        with patch.object(
            auth_service,
            "add_user_to_family",
            new_callable=AsyncMock,
            side_effect=RuntimeError("simulated failure"),
        ):
            with pytest.raises(RuntimeError, match="simulated failure"):
                await auth_service.initial_setup(
                    db, "fail@example.com", "password123", "Admin", "Fail Family"
                )

        await db.rollback()

        # Nothing should persist
        result = await db.execute(select(User).where(User.email == "fail@example.com"))
        assert result.scalar_one_or_none() is None

        result = await db.execute(select(Family).where(Family.name == "Fail Family"))
        assert result.scalar_one_or_none() is None


class TestRegisterWithFamilyCodeAtomicity:
    """Verify register_with_family_code is atomic."""

    async def test_register_new_user_succeeds(self, db: AsyncSession):
        """Happy path: new user registers with a family code."""
        # Create a family first
        family = await auth_service.create_family(db, "Join Family")
        await db.commit()

        user, error, session_token = await auth_service.register_with_family_code(
            db, family.family_code, "newuser@example.com", "password123", "New User"
        )
        await db.commit()

        assert error is None
        assert user is not None
        assert session_token is not None
        assert user.current_family_id == family.id

    async def test_register_failure_mid_flow_leaves_nothing(self, db: AsyncSession):
        """If create_session fails during registration, no user should persist."""
        family = await auth_service.create_family(db, "Fail Join Family")
        await db.commit()

        # Capture ID before rollback invalidates the object
        family_id = family.id

        with patch.object(
            auth_service,
            "create_session",
            new_callable=AsyncMock,
            side_effect=RuntimeError("simulated session failure"),
        ):
            with pytest.raises(RuntimeError, match="simulated session failure"):
                await auth_service.register_with_family_code(
                    db,
                    family.family_code,
                    "failregister@example.com",
                    "password123",
                    "Fail User",
                )

        await db.rollback()

        # User should not persist
        result = await db.execute(select(User).where(User.email == "failregister@example.com"))
        assert result.scalar_one_or_none() is None

        # No membership for the family (only the family itself should persist from before)
        result = await db.execute(
            select(FamilyMembership).where(FamilyMembership.family_id == family_id)
        )
        memberships = result.scalars().all()
        assert len(memberships) == 0
