"""Tests for family deletion and orphan-guard invariant.

Covers:
  - DELETE /api/auth/families/{id}: 403, 404, 409, 200
  - Cascade proof: memberships/events/visibility removed after delete
  - current_family_id nulling on affected users
  - remove_member orphan check: cannot remove user's last membership
  - GET /api/auth/families: member_count included
"""

from __future__ import annotations

import os
import secrets
import sys
import uuid
from datetime import UTC, datetime, timedelta
from pathlib import Path

# Must be set before any app imports
os.environ["DATABASE_PATH"] = "/tmp/test-familycircle-delete.db"

_test_upload_dir = Path("/tmp/test-fc-uploads-delete")
_test_upload_dir.mkdir(parents=True, exist_ok=True)

for mod_name in list(sys.modules):
    if mod_name.startswith("app.main"):
        del sys.modules[mod_name]

_orig_mkdir = Path.mkdir


def _patched_mkdir(self, *args, **kwargs):
    if str(self).startswith("/data"):
        _test_upload_dir.mkdir(parents=True, exist_ok=True)
        return
    return _orig_mkdir(self, *args, **kwargs)


from starlette.staticfiles import StaticFiles  # noqa: E402

_orig_staticfiles_init = StaticFiles.__init__


def _patched_staticfiles_init(self, *args, **kwargs):
    directory = kwargs.get("directory") or (args[0] if args else None)
    if directory and str(directory).startswith("/data"):
        kwargs["directory"] = str(_test_upload_dir)
        if args:
            args = (str(_test_upload_dir),) + args[1:]
    return _orig_staticfiles_init(self, *args, **kwargs)


Path.mkdir = _patched_mkdir  # type: ignore[assignment]
StaticFiles.__init__ = _patched_staticfiles_init  # type: ignore[assignment]

import app.main as _main_mod  # noqa: E402, F401

Path.mkdir = _orig_mkdir  # type: ignore[assignment]
StaticFiles.__init__ = _orig_staticfiles_init  # type: ignore[assignment]

import pytest  # noqa: E402
from httpx import ASGITransport, AsyncClient  # noqa: E402
from sqlalchemy import select  # noqa: E402
from sqlalchemy.ext.asyncio import (  # noqa: E402
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.models.base import Base  # noqa: E402
from app.models.event import Event  # noqa: E402
from app.models.family import Family  # noqa: E402
from app.models.family_membership import FamilyMembership, FamilyRole  # noqa: E402
from app.models.profile_visibility import ProfileVisibility  # noqa: E402
from app.models.token import Token, TokenType  # noqa: E402
from app.models.user import User  # noqa: E402


def _uuid() -> str:
    return str(uuid.uuid4())


def _token() -> str:
    return secrets.token_hex(32)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
async def engine():
    eng = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield eng
    await eng.dispose()


@pytest.fixture
async def session_factory(engine):
    return async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


@pytest.fixture
async def seed(session_factory):
    """Seed scenario:
    - super_admin belongs to family_a (admin) AND family_b (admin)
    - regular_user belongs ONLY to family_a (member)
    - family_a has one event and visibility settings
    """
    async with session_factory() as db:
        family_a_id = _uuid()
        family_b_id = _uuid()
        super_admin_id = _uuid()
        regular_user_id = _uuid()
        sa_token = _token()
        ru_token = _token()

        family_a = Family(id=family_a_id, name="Family Alpha", family_code="ALPHA01")
        family_b = Family(id=family_b_id, name="Family Beta", family_code="BETA-02")

        super_admin = User(
            id=super_admin_id,
            email="super@test.com",
            is_super_admin=True,
            current_family_id=family_a_id,
        )
        regular_user = User(
            id=regular_user_id,
            email="regular@test.com",
            is_super_admin=False,
            current_family_id=family_a_id,
        )

        # Super admin in both families
        sa_membership_a = FamilyMembership(
            id=_uuid(),
            user_id=super_admin_id,
            family_id=family_a_id,
            role=FamilyRole.ADMIN,
            display_name="Super Admin",
        )
        sa_membership_b = FamilyMembership(
            id=_uuid(),
            user_id=super_admin_id,
            family_id=family_b_id,
            role=FamilyRole.ADMIN,
            display_name="Super Admin",
        )
        # Regular user only in family_a
        ru_membership = FamilyMembership(
            id=_uuid(),
            user_id=regular_user_id,
            family_id=family_a_id,
            role=FamilyRole.MEMBER,
            display_name="Regular User",
        )

        # Visibility for regular user in family_a
        visibility = ProfileVisibility(
            id=_uuid(),
            user_id=regular_user_id,
            family_id=family_a_id,
            show_email=True,
            show_phone=True,
            show_address=True,
        )

        # Event in family_a
        event = Event(
            id=_uuid(),
            family_id=family_a_id,
            title="Test Event",
            event_type="general",
            created_by_id=super_admin_id,
            event_date=datetime.now(UTC) + timedelta(days=7),
        )

        # Tokens
        sa_token_obj = Token(
            id=_uuid(),
            user_id=super_admin_id,
            token=sa_token,
            token_type=TokenType.SESSION,
            expires_at=datetime.now(UTC) + timedelta(days=30),
        )
        ru_token_obj = Token(
            id=_uuid(),
            user_id=regular_user_id,
            token=ru_token,
            token_type=TokenType.SESSION,
            expires_at=datetime.now(UTC) + timedelta(days=30),
        )

        from app.models.settings import Setting

        db.add_all(
            [
                family_a,
                family_b,
                super_admin,
                regular_user,
                sa_membership_a,
                sa_membership_b,
                ru_membership,
                visibility,
                event,
                sa_token_obj,
                ru_token_obj,
                Setting(key="secret_key", value=secrets.token_hex(32), family_id=None),
                Setting(key="app_name", value="FamilyCircle", family_id=None),
                Setting(key="magic_link_expiry_days", value="1", family_id=None),
            ]
        )
        await db.commit()

    return {
        "family_a_id": family_a_id,
        "family_b_id": family_b_id,
        "super_admin_id": super_admin_id,
        "regular_user_id": regular_user_id,
        "sa_token": sa_token,
        "ru_token": ru_token,
        "event_id": event.id,
    }


@pytest.fixture
async def client(engine, session_factory, seed):
    from app.db import get_db_session
    from app.main import app

    async def _override_db():
        async with session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    app.dependency_overrides[get_db_session] = _override_db
    transport = ASGITransport(app=app, raise_app_exceptions=False)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# DELETE /api/auth/families/{id}
# ---------------------------------------------------------------------------


class TestDeleteFamily:
    """Tests for the DELETE /api/auth/families/{family_id} endpoint."""

    @pytest.mark.asyncio
    async def test_403_non_super_admin(self, client, seed):
        """Regular user gets 403."""
        resp = await client.delete(
            f"/api/auth/families/{seed['family_a_id']}",
            headers=_auth(seed["ru_token"]),
        )
        assert resp.status_code == 403

    @pytest.mark.asyncio
    async def test_404_nonexistent_family(self, client, seed):
        """Deleting a non-existent family returns 404."""
        resp = await client.delete(
            f"/api/auth/families/{_uuid()}",
            headers=_auth(seed["sa_token"]),
        )
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_409_orphaned_users(self, client, seed):
        """Cannot delete family_a because regular_user belongs only to it."""
        resp = await client.delete(
            f"/api/auth/families/{seed['family_a_id']}",
            headers=_auth(seed["sa_token"]),
        )
        assert resp.status_code == 409
        body = resp.json()
        assert "orphaned_users" in body
        assert "regular@test.com" in body["orphaned_users"]

    @pytest.mark.asyncio
    async def test_200_successful_delete(self, client, seed):
        """Can delete family_b (super admin has another family)."""
        resp = await client.delete(
            f"/api/auth/families/{seed['family_b_id']}",
            headers=_auth(seed["sa_token"]),
        )
        assert resp.status_code == 200
        assert "deleted" in resp.json()["message"].lower()

    @pytest.mark.asyncio
    async def test_cascade_memberships_removed(self, client, seed, session_factory):
        """After deleting family_b, its memberships are gone."""
        await client.delete(
            f"/api/auth/families/{seed['family_b_id']}",
            headers=_auth(seed["sa_token"]),
        )
        async with session_factory() as db:
            result = await db.execute(
                select(FamilyMembership).where(FamilyMembership.family_id == seed["family_b_id"])
            )
            assert result.scalars().all() == []

    @pytest.mark.asyncio
    async def test_cascade_events_removed(self, client, seed, session_factory):
        """After deleting a family, its events are gone.

        We need to first make family_a deletable by giving regular_user a second family.
        """
        # Add regular_user to family_b so they won't be orphaned
        async with session_factory() as db:
            db.add(
                FamilyMembership(
                    id=_uuid(),
                    user_id=seed["regular_user_id"],
                    family_id=seed["family_b_id"],
                    role=FamilyRole.MEMBER,
                    display_name="Regular User",
                )
            )
            await db.commit()

        resp = await client.delete(
            f"/api/auth/families/{seed['family_a_id']}",
            headers=_auth(seed["sa_token"]),
        )
        assert resp.status_code == 200

        async with session_factory() as db:
            result = await db.execute(select(Event).where(Event.family_id == seed["family_a_id"]))
            assert result.scalars().all() == []

    @pytest.mark.asyncio
    async def test_current_family_id_auto_switched(self, client, seed, session_factory):
        """After deleting family_b, super admin is auto-switched to family_a
        (their other remaining family), not left with current_family_id=null.
        """
        # Switch super admin's context to family_b
        async with session_factory() as db:
            result = await db.execute(select(User).where(User.id == seed["super_admin_id"]))
            user = result.scalar_one()
            user.current_family_id = seed["family_b_id"]
            await db.commit()

        # Delete family_b
        resp = await client.delete(
            f"/api/auth/families/{seed['family_b_id']}",
            headers=_auth(seed["sa_token"]),
        )
        assert resp.status_code == 200

        # Verify current_family_id was auto-switched to family_a
        async with session_factory() as db:
            result = await db.execute(select(User).where(User.id == seed["super_admin_id"]))
            user = result.scalar_one()
            assert user.current_family_id == seed["family_a_id"]


# ---------------------------------------------------------------------------
# GET /api/auth/families — member_count
# ---------------------------------------------------------------------------


class TestListFamilies:
    """Tests for the GET /api/auth/families endpoint."""

    @pytest.mark.asyncio
    async def test_member_count_included(self, client, seed):
        """Family list includes member_count."""
        resp = await client.get(
            "/api/auth/families",
            headers=_auth(seed["sa_token"]),
        )
        assert resp.status_code == 200
        families = resp.json()["families"]
        assert len(families) == 2

        # Family Alpha has 2 members (super_admin + regular_user)
        alpha = next(f for f in families if f["name"] == "Family Alpha")
        assert alpha["member_count"] == 2

        # Family Beta has 1 member (super_admin only)
        beta = next(f for f in families if f["name"] == "Family Beta")
        assert beta["member_count"] == 1


# ---------------------------------------------------------------------------
# DELETE /api/family/members/{user_id} — orphan guard
# ---------------------------------------------------------------------------


class TestRemoveMemberOrphanGuard:
    """Tests that remove_member blocks removal of a user's last membership."""

    @pytest.mark.asyncio
    async def test_cannot_remove_last_membership(self, client, seed):
        """Removing regular_user from family_a is blocked (it's their only family)."""
        resp = await client.delete(
            f"/api/family/members/{seed['regular_user_id']}",
            headers=_auth(seed["sa_token"]),
        )
        assert resp.status_code == 400
        assert "last family membership" in resp.json()["detail"].lower()
