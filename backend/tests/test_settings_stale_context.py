"""Security regression tests for GET /api/settings stale family context (F2 follow-up).

The settings endpoint uses get_optional_user and reads the family context directly,
bypassing require_family_context. A removed member with a stale current_family_id
must not keep reading their old family's settings.
"""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.api.settings import get_settings
from app.services import auth as auth_service


class TestSettingsStaleContext:
    async def test_stale_member_gets_no_family_settings(self, db: AsyncSession):
        """current_family_id pointing at a non-member family yields no family settings."""
        family = await auth_service.create_family(db, "Fam")
        user = await auth_service.create_user(db, "stale@test.com", "pw123456")
        user.current_family_id = family.id  # stale: user is NOT a member
        await db.commit()

        result = await get_settings(user=user, db=db)
        assert "theme_color" not in result["settings"]

    async def test_live_member_gets_family_settings(self, db: AsyncSession):
        """A live member still receives the family settings."""
        family = await auth_service.create_family(db, "Fam")
        user = await auth_service.create_user(db, "live@test.com", "pw123456")
        await auth_service.add_user_to_family(db, user, family, "Live")
        user.current_family_id = family.id
        await db.commit()

        result = await get_settings(user=user, db=db)
        assert result["settings"]["theme_color"] == "teal"

    async def test_no_family_context_gets_no_family_settings(self, db: AsyncSession):
        """A user with no current family gets only public settings (no raise)."""
        user = await auth_service.create_user(db, "none@test.com", "pw123456")
        await db.commit()

        result = await get_settings(user=user, db=db)
        assert "theme_color" not in result["settings"]
