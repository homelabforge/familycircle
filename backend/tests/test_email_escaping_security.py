"""Regression tests: user content is HTML-escaped in email/notification bodies (F12)."""

from __future__ import annotations

from unittest.mock import patch

from sqlalchemy.ext.asyncio import AsyncSession

from app.services import email as email_service
from app.services.notifications.email_service import EmailNotificationService


class TestTemplateEmailEscaping:
    async def test_event_cancelled_escapes_html_in_body_not_subject(self, db: AsyncSession):
        captured: dict[str, str] = {}

        async def fake_send_email(db, to_email, subject, body_html, body_text=None):
            captured["html"] = body_html
            captured["subject"] = subject
            return True

        with patch.object(email_service, "send_email", side_effect=fake_send_email):
            await email_service.send_event_cancelled_email(
                db=db,
                to_email="x@test.com",
                recipient_name="Bob",
                event_title='<a href="http://evil.test">Party</a>',
                event_date="2026-01-01",
                cancellation_reason="<script>alert(1)</script>",
                cancelled_by="Admin",
            )

        # HTML body is escaped...
        assert "&lt;a href=" in captured["html"]
        assert "&lt;script&gt;" in captured["html"]
        assert '<a href="http://evil.test">Party</a>' not in captured["html"]
        # ...the subject is a plain-text header and stays raw (not HTML-escaped).
        assert "<a href=" in captured["subject"]

    async def test_invitation_escapes_inviter_and_family(self, db: AsyncSession):
        captured: dict[str, str] = {}

        async def fake_send_email(db, to_email, subject, body_html, body_text=None):
            captured["html"] = body_html
            return True

        with patch.object(email_service, "send_email", side_effect=fake_send_email):
            await email_service.send_family_invitation_email(
                db=db,
                to_email="x@test.com",
                inviter_name="<b>Eve</b>",
                family_name="<img src=x onerror=alert(1)>",
                family_code="ABCDEF-12",
                base_url="https://t.test",
            )

        assert "&lt;b&gt;Eve&lt;/b&gt;" in captured["html"]
        assert "<img src=x" not in captured["html"]


class TestNotificationEmailEscaping:
    async def test_html_body_escapes_title_and_message(self):
        svc = EmailNotificationService(
            smtp_host="h",
            smtp_port=587,
            smtp_username="u",
            smtp_password="p",
            from_email="f@test.com",
            to_email="t@test.com",
        )
        captured: dict[str, str] = {}

        async def fake_send(msg, **kwargs):
            for part in msg.walk():
                if part.get_content_type() == "text/html":
                    captured["html"] = part.get_payload(decode=True).decode()
            return {}

        with patch("aiosmtplib.send", side_effect=fake_send):
            await svc.send(
                title="<b>hi</b>",
                message="<script>alert(1)</script>",
                url='http://x"onmouseover="evil',
            )

        assert "&lt;b&gt;hi&lt;/b&gt;" in captured["html"]
        assert "<script>alert(1)</script>" not in captured["html"]
        # The href value is quote-escaped so it can't break out of the attribute.
        assert '"onmouseover=' not in captured["html"]
