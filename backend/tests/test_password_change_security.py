"""Security regression tests for session invalidation on password change/reset (F5).

Password change (self-service) and admin reset must invalidate existing tokens —
a pre-existing session must not survive the credential change (CWE-613).
"""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth import admin_reset_password
from app.models.family_membership import FamilyRole
from app.schemas.auth import AdminResetPasswordRequest
from app.services import auth as auth_service


class TestChangePasswordInvalidatesSessions:
    async def test_old_session_rejected_new_session_valid(self, db: AsyncSession):
        """change_password kills the old session and returns a fresh working one."""
        family = await auth_service.create_family(db, "Fam")
        user = await auth_service.create_user(db, "u@test.com", "oldpass1")
        await auth_service.add_user_to_family(db, user, family, "U")
        user.current_family_id = family.id
        old_token = await auth_service.create_session(user, db)
        await db.commit()

        assert await auth_service.get_user_by_session(db, old_token) is not None

        new_token = await auth_service.change_password(db, user, "oldpass1", "newpass1")
        await db.commit()

        assert new_token is not None
        assert new_token != old_token
        assert await auth_service.get_user_by_session(db, old_token) is None
        assert await auth_service.get_user_by_session(db, new_token) is not None

    async def test_magic_link_invalidated_on_change(self, db: AsyncSession):
        """A live magic-link reset token must not survive a password change."""
        family = await auth_service.create_family(db, "Fam")
        user = await auth_service.create_user(db, "u@test.com", "oldpass1")
        await auth_service.add_user_to_family(db, user, family, "U")
        await db.commit()

        result = await auth_service.create_magic_link(db, "u@test.com")
        await db.commit()
        assert result is not None
        magic_token, _ = result
        assert await auth_service.get_user_by_magic_token(db, magic_token) is not None

        await auth_service.change_password(db, user, "oldpass1", "newpass1")
        await db.commit()
        assert await auth_service.get_user_by_magic_token(db, magic_token) is None

    async def test_wrong_current_password_keeps_session(self, db: AsyncSession):
        """A failed change (wrong current password) returns None and revokes nothing."""
        family = await auth_service.create_family(db, "Fam")
        user = await auth_service.create_user(db, "u@test.com", "oldpass1")
        await auth_service.add_user_to_family(db, user, family, "U")
        token = await auth_service.create_session(user, db)
        await db.commit()

        result = await auth_service.change_password(db, user, "WRONGPASS", "newpass1")
        assert result is None
        assert await auth_service.get_user_by_session(db, token) is not None


class TestAdminResetInvalidatesTargetSessions:
    async def test_admin_reset_revokes_target_tokens(self, db: AsyncSession):
        """An admin reset locks the target out by revoking their sessions."""
        family = await auth_service.create_family(db, "Fam")
        admin = await auth_service.create_user(db, "admin@test.com", "pw123456")
        await auth_service.add_user_to_family(db, admin, family, "Admin", FamilyRole.ADMIN)
        admin.current_family_id = family.id
        member = await auth_service.create_user(db, "member@test.com", "pw123456")
        await auth_service.add_user_to_family(db, member, family, "Member", FamilyRole.MEMBER)
        member.current_family_id = family.id
        member_token = await auth_service.create_session(member, db)
        await db.commit()

        assert await auth_service.get_user_by_session(db, member_token) is not None

        await admin_reset_password(
            request=AdminResetPasswordRequest(user_id=member.id, new_password="newpass1"),
            admin=admin,
            db=db,
        )
        # Handler is flush-only; the DELETE executes within the open transaction.
        assert await auth_service.get_user_by_session(db, member_token) is None
