"""Security regression tests for family-code disclosure (F4).

The family join code is a secret enrolment control. It must NOT appear in
general auth responses (/me, /login, /register, /switch-family) where any
member could read and share it. It remains available only via the admin-only
family-code endpoints.
"""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth import build_user_response, get_current_user_info
from app.api.settings import get_family_code as settings_get_family_code
from app.models.family_membership import FamilyRole
from app.schemas.auth import FamilyInfo, UserResponse, UserWithFamilyContext
from app.services import auth as auth_service


class TestFamilyCodeNotInGeneralResponses:
    def test_family_info_schema_has_no_family_code(self):
        """The reused FamilyInfo schema must not declare family_code."""
        assert "family_code" not in FamilyInfo.model_fields

    def test_user_response_schemas_have_no_family_code(self):
        """Neither response schema leaks the code at the top level."""
        assert "family_code" not in UserResponse.model_fields
        assert "family_code" not in UserWithFamilyContext.model_fields

    async def test_get_user_families_info_omits_family_code(self, db: AsyncSession):
        """The service helper no longer serializes the code per family."""
        family = await auth_service.create_family(db, "Family")
        user = await auth_service.create_user(db, "member@test.com", "pw123456")
        await auth_service.add_user_to_family(db, user, family, "Member")
        user.current_family_id = family.id
        await db.commit()

        loaded = await auth_service.get_user_by_id_with_families(db, user.id)
        assert loaded is not None
        families = auth_service.get_user_families_info(loaded)
        assert families  # not empty
        for fam in families:
            assert "family_code" not in fam

    async def test_me_response_omits_family_code(self, db: AsyncSession):
        """A non-admin /me response carries no family_code for any family."""
        family = await auth_service.create_family(db, "Family")
        user = await auth_service.create_user(db, "member@test.com", "pw123456")
        await auth_service.add_user_to_family(db, user, family, "Member")
        user.current_family_id = family.id
        await db.commit()

        response = await get_current_user_info(user=user, db=db)
        assert response["families"]
        for fam in response["families"]:
            assert "family_code" not in fam

    async def test_build_user_response_omits_family_code(self, db: AsyncSession):
        """build_user_response (shared by login/register/switch) omits the code."""
        family = await auth_service.create_family(db, "Family")
        user = await auth_service.create_user(db, "member@test.com", "pw123456")
        await auth_service.add_user_to_family(db, user, family, "Member")
        user.current_family_id = family.id
        await db.commit()

        loaded = await auth_service.get_user_by_id_with_families(db, user.id)
        assert loaded is not None
        response = build_user_response(loaded)
        for fam in response["families"]:
            assert "family_code" not in fam


class TestFamilyCodeStillAvailableToAdmins:
    async def test_admin_family_code_endpoint_still_returns_code(self, db: AsyncSession):
        """The admin-only /settings/family-code endpoint still discloses the code."""
        family = await auth_service.create_family(db, "Family")
        admin = await auth_service.create_user(db, "admin@test.com", "pw123456")
        await auth_service.add_user_to_family(db, admin, family, "Admin", FamilyRole.ADMIN)
        admin.current_family_id = family.id
        await db.commit()

        result = await settings_get_family_code(user=admin, db=db)
        assert result["code"] == family.family_code
