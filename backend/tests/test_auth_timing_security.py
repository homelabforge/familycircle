"""Regression tests for auth timing-enumeration mitigations (F13).

Lightweight (no wall-clock assertions): confirm the login miss path still runs a
password verify, and that forgot-password schedules the SMTP send off-request via
a background task.
"""

from __future__ import annotations

from unittest.mock import Mock, patch

from argon2.exceptions import VerifyMismatchError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.services import auth as auth_service


class TestLoginMissPathConstantTime:
    async def test_unknown_email_still_runs_a_verify(self, db: AsyncSession):
        # argon2's PasswordHasher.verify is read-only, so patch the whole hasher.
        with patch.object(auth_service, "ph") as mock_ph:
            mock_ph.verify.side_effect = VerifyMismatchError()
            user, token = await auth_service.verify_password(db, "nobody@test.com", "whatever")
        assert user is None and token is None
        assert mock_ph.verify.called  # dummy verify ran on the miss path

    async def test_passwordless_account_still_runs_a_verify(self, db: AsyncSession):
        db.add(User(email="oidc@test.com", password_hash=None))
        await db.commit()
        with patch.object(auth_service, "ph") as mock_ph:
            mock_ph.verify.side_effect = VerifyMismatchError()
            user, token = await auth_service.verify_password(db, "oidc@test.com", "whatever")
        assert user is None and token is None
        assert mock_ph.verify.called


class TestForgotPasswordBackgroundSend:
    async def test_schedules_email_as_background_task(self, db: AsyncSession, monkeypatch):
        from fastapi import BackgroundTasks

        from app.api import auth as auth_api
        from app.schemas.auth import ForgotPasswordRequest

        family = await auth_service.create_family(db, "Fam")
        user = await auth_service.create_user(db, "u@test.com", "pw123456")
        await auth_service.add_user_to_family(db, user, family, "U")
        # Configure SMTP so the send branch (not the dev-token branch) is taken.
        await auth_service.set_setting(db, "smtp_host", "smtp.test")
        await auth_service.set_setting(db, "smtp_password", "secret")
        await auth_service.set_setting(db, "smtp_from_email", "from@test.com")
        await db.commit()

        monkeypatch.setattr("app.config.PUBLIC_BASE_URL", "https://t.test")
        bg = BackgroundTasks()

        # Bypass the slowapi rate-limit decorator via __wrapped__ (getattr keeps
        # the type checker happy about the runtime-only attribute).
        unwrapped = getattr(auth_api.forgot_password, "__wrapped__")
        result = await unwrapped(
            request=Mock(),
            body=ForgotPasswordRequest(email="u@test.com"),
            background_tasks=bg,
            db=db,
        )

        assert "If an account exists" in result["message"]
        assert len(bg.tasks) == 1
        assert bg.tasks[0].func is auth_api._send_password_reset_email_bg

    async def test_no_dev_token_leaked_when_smtp_configured(self, db: AsyncSession, monkeypatch):
        from fastapi import BackgroundTasks

        from app.api import auth as auth_api
        from app.schemas.auth import ForgotPasswordRequest

        family = await auth_service.create_family(db, "Fam")
        user = await auth_service.create_user(db, "u2@test.com", "pw123456")
        await auth_service.add_user_to_family(db, user, family, "U")
        await auth_service.set_setting(db, "smtp_host", "smtp.test")
        await auth_service.set_setting(db, "smtp_password", "secret")
        await auth_service.set_setting(db, "smtp_from_email", "from@test.com")
        await db.commit()

        monkeypatch.setattr("app.config.PUBLIC_BASE_URL", "https://t.test")
        unwrapped = getattr(auth_api.forgot_password, "__wrapped__")
        result = await unwrapped(
            request=Mock(),
            body=ForgotPasswordRequest(email="u2@test.com"),
            background_tasks=BackgroundTasks(),
            db=db,
        )
        assert "dev_token" not in result
