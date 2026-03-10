"""Email notification service wrapping FamilyCircle's existing SMTP infrastructure."""

import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import aiosmtplib

from app.services.notifications.base import NotificationService

logger = logging.getLogger(__name__)


class EmailNotificationService(NotificationService):
    """Email notification service using existing SMTP configuration."""

    service_name = "email"

    def __init__(
        self,
        smtp_host: str,
        smtp_port: int,
        smtp_username: str,
        smtp_password: str,
        from_email: str,
        to_email: str,
        use_tls: bool = True,
    ) -> None:
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.smtp_username = smtp_username
        self.smtp_password = smtp_password
        self.from_email = from_email
        self.to_email = to_email
        self.use_tls = use_tls

    async def close(self) -> None:
        """No persistent connection to close."""
        pass

    async def send(
        self,
        title: str,
        message: str,
        priority: str = "default",
        tags: list[str] | None = None,
        url: str | None = None,
    ) -> bool:
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = f"[FamilyCircle] {title}"
            msg["From"] = f"FamilyCircle <{self.from_email}>"
            msg["To"] = self.to_email

            # Build plain text body
            body_text = f"{title}\n\n{message}"
            if url:
                body_text += f"\n\nView: {url}"

            # Build HTML body
            priority_color = {
                "min": "#808080",
                "low": "#36a64f",
                "default": "#4f46e5",
                "high": "#FF9800",
                "urgent": "#F44336",
            }.get(priority, "#4f46e5")

            body_html = f"""
<div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 600px; margin: 0 auto;">
    <div style="border-top: 3px solid {priority_color}; padding: 20px;">
        <h2 style="color: {priority_color}; margin: 0 0 15px 0;">{title}</h2>
        <p style="color: #333; line-height: 1.6;">{message}</p>
        {f'<p><a href="{url}" style="color: {priority_color};">View Details</a></p>' if url else ""}
    </div>
    <div style="text-align: center; padding: 15px; color: #6b7280; font-size: 12px; border-top: 1px solid #e5e7eb;">
        Sent by FamilyCircle
    </div>
</div>"""

            msg.attach(MIMEText(body_text, "plain"))
            msg.attach(MIMEText(body_html, "html"))

            if self.use_tls:
                await aiosmtplib.send(
                    msg,
                    hostname=self.smtp_host,
                    port=self.smtp_port,
                    username=self.smtp_username,
                    password=self.smtp_password,
                    start_tls=True,
                )
            else:
                await aiosmtplib.send(
                    msg,
                    hostname=self.smtp_host,
                    port=self.smtp_port,
                    username=self.smtp_username,
                    password=self.smtp_password,
                )

            logger.info("[email] Sent notification to %s: %s", self.to_email, title)
            return True

        except aiosmtplib.SMTPException as e:
            logger.error("[email] SMTP error: %s", e)
            return False
        except OSError as e:
            logger.error("[email] Connection error: %s", e)
            return False

    async def test_connection(self) -> tuple[bool, str]:
        try:
            success = await self.send(
                title="Test Notification",
                message="This is a test notification from FamilyCircle.",
                priority="low",
            )

            if success:
                return True, f"Test email sent to {self.to_email}"
            return False, "Failed to send test email"

        except Exception as e:
            return False, f"Connection test failed: {str(e)}"
