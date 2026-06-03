"""Security regression tests for register-with-family-code (F1).

The existing-account branch of registration must never mint a session for an
account without proving control of it. Email + a valid family code is NOT proof
of account ownership (CWE-287 / account takeover).
"""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.token import Token, TokenType
from app.models.user import User
from app.services import auth as auth_service


async def _session_token_count(db: AsyncSession, user_id: str | None = None) -> int:
    stmt = select(func.count()).select_from(Token).where(Token.token_type == TokenType.SESSION)
    if user_id is not None:
        stmt = stmt.where(Token.user_id == user_id)
    return (await db.execute(stmt)).scalar() or 0


class TestRegisterExistingAccount:
    """Existing-email registration cannot take over the account."""

    async def test_wrong_password_mints_no_session(self, db: AsyncSession):
        """Victim email + valid code + WRONG password → 4xx, zero new tokens."""
        family_a = await auth_service.create_family(db, "Family A")
        victim = await auth_service.create_user(db, "victim@test.com", "correct-horse")
        await auth_service.add_user_to_family(db, victim, family_a, "Victim")
        family_b = await auth_service.create_family(db, "Family B")
        await db.commit()

        tokens_before = await _session_token_count(db)

        user, error, token = await auth_service.register_with_family_code(
            db, family_b.family_code, "victim@test.com", "wrong-password", "Attacker"
        )

        assert user is None
        assert token is None
        assert error is not None
        # No session was minted for anyone
        assert await _session_token_count(db) == tokens_before
        # Victim was NOT silently added to family B
        assert await auth_service.get_user_membership(db, victim.id, family_b.id) is None

    async def test_correct_password_joins_and_mints_one_session(self, db: AsyncSession):
        """Existing user + CORRECT password joins the family with exactly one session."""
        family_a = await auth_service.create_family(db, "Family A")
        member = await auth_service.create_user(db, "member@test.com", "correct-horse")
        await auth_service.add_user_to_family(db, member, family_a, "Member")
        family_b = await auth_service.create_family(db, "Family B")
        await db.commit()

        user, error, token = await auth_service.register_with_family_code(
            db, family_b.family_code, "member@test.com", "correct-horse", "Member B"
        )
        await db.commit()

        assert error is None
        assert user is not None
        assert token is not None
        assert user.current_family_id == family_b.id
        assert await _session_token_count(db, member.id) == 1
        assert await auth_service.get_user_membership(db, member.id, family_b.id) is not None

    async def test_oidc_only_account_cannot_be_linked(self, db: AsyncSession):
        """An account with no local password (OIDC-only) cannot be linked via register."""
        family_a = await auth_service.create_family(db, "Family A")
        oidc_user = User(email="oidc@test.com", password_hash=None)
        db.add(oidc_user)
        await db.flush()
        await auth_service.add_user_to_family(db, oidc_user, family_a, "Oidc")
        family_b = await auth_service.create_family(db, "Family B")
        await db.commit()

        tokens_before = await _session_token_count(db)

        user, error, token = await auth_service.register_with_family_code(
            db, family_b.family_code, "oidc@test.com", "anything", "Oidc B"
        )

        assert user is None
        assert token is None
        assert error is not None
        assert await _session_token_count(db) == tokens_before
        assert await auth_service.get_user_membership(db, oidc_user.id, family_b.id) is None

    async def test_existing_member_still_blocked(self, db: AsyncSession):
        """Re-registering into a family you already belong to is still refused."""
        family = await auth_service.create_family(db, "Family")
        member = await auth_service.create_user(db, "already@test.com", "pw123456")
        await auth_service.add_user_to_family(db, member, family, "Already")
        await db.commit()

        user, error, token = await auth_service.register_with_family_code(
            db, family.family_code, "already@test.com", "pw123456", "Already"
        )

        assert user is None
        assert token is None
        assert error is not None
        assert "already a member" in error.lower()

    async def test_new_user_registration_unaffected(self, db: AsyncSession):
        """A brand-new email still registers and gets a session (no regression)."""
        family = await auth_service.create_family(db, "Family")
        await db.commit()

        user, error, token = await auth_service.register_with_family_code(
            db, family.family_code, "brandnew@test.com", "pw123456", "New User"
        )
        await db.commit()

        assert error is None
        assert user is not None
        assert token is not None
        assert user.current_family_id == family.id
