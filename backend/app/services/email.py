"""Email service for FamilyCircle.

Handles sending emails for:
- Password reset
- Family invitations
- Event cancellation notifications
"""

import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import aiosmtplib
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.settings_service import SettingsService, SmtpConfig

logger = logging.getLogger(__name__)


async def get_smtp_config(db: AsyncSession) -> SmtpConfig:
    """Load SMTP configuration from database settings."""
    return await SettingsService(db).get_smtp_config()


async def get_app_name(db: AsyncSession) -> str:
    """Get the app name from settings."""
    config = await SettingsService(db).get_app_config()
    return config.app_name


async def send_email(
    db: AsyncSession,
    to_email: str,
    subject: str,
    body_html: str,
    body_text: str | None = None,
) -> bool:
    """
    Send an email using configured SMTP settings.

    Returns True if email was sent successfully, False otherwise.
    If SMTP is not configured, logs the email content instead.
    """
    config = await get_smtp_config(db)

    if not config.is_configured:
        # Log email instead of sending (development mode)
        logger.info(
            "[EMAIL NOT SENT - SMTP not configured] To: %s, Subject: %s",
            to_email,
            subject,
        )
        return False

    try:
        # Create message
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f"{config.from_name} <{config.from_email}>"
        msg["To"] = to_email

        # Add plain text version
        if body_text:
            msg.attach(MIMEText(body_text, "plain"))

        # Add HTML version
        msg.attach(MIMEText(body_html, "html"))

        # Send email
        if config.use_tls:
            await aiosmtplib.send(
                msg,
                hostname=config.host,
                port=config.port,
                username=config.username,
                password=config.password,
                start_tls=True,
            )
        else:
            await aiosmtplib.send(
                msg,
                hostname=config.host,
                port=config.port,
                username=config.username,
                password=config.password,
            )

        logger.info("Email sent successfully to %s: %s", to_email, subject)
        return True

    except Exception as e:
        logger.error("Failed to send email to %s: %s", to_email, type(e).__name__)
        return False


# =============================================================================
# Email Templates
# =============================================================================


def _base_template(content: str, app_name: str) -> str:
    """Wrap content in base HTML email template."""
    return f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
        }}
        .header {{
            text-align: center;
            padding: 20px 0;
            border-bottom: 2px solid #4f46e5;
        }}
        .header h1 {{
            color: #4f46e5;
            margin: 0;
            font-size: 24px;
        }}
        .content {{
            padding: 30px 0;
        }}
        .button {{
            display: inline-block;
            background-color: #4f46e5;
            color: white !important;
            text-decoration: none;
            padding: 12px 30px;
            border-radius: 8px;
            font-weight: 600;
            margin: 20px 0;
        }}
        .button:hover {{
            background-color: #4338ca;
        }}
        .code {{
            font-family: monospace;
            font-size: 24px;
            font-weight: bold;
            color: #4f46e5;
            background: #f3f4f6;
            padding: 15px 25px;
            border-radius: 8px;
            display: inline-block;
            letter-spacing: 2px;
        }}
        .footer {{
            text-align: center;
            padding-top: 20px;
            border-top: 1px solid #e5e7eb;
            color: #6b7280;
            font-size: 14px;
        }}
        .warning {{
            background: #fef3c7;
            border: 1px solid #f59e0b;
            border-radius: 8px;
            padding: 15px;
            margin: 20px 0;
        }}
        .cancelled {{
            background: #fee2e2;
            border: 1px solid #ef4444;
            border-radius: 8px;
            padding: 15px;
            margin: 20px 0;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>{app_name}</h1>
    </div>
    <div class="content">
        {content}
    </div>
    <div class="footer">
        <p>This email was sent by {app_name}.</p>
        <p>If you didn't expect this email, you can safely ignore it.</p>
    </div>
</body>
</html>
"""


# =============================================================================
# Specific Email Functions
# =============================================================================


async def send_password_reset_email(
    db: AsyncSession,
    to_email: str,
    reset_token: str,
    base_url: str,
    expiry_days: int = 1,
) -> bool:
    """Send password reset email with reset link."""
    app_name = await get_app_name(db)
    reset_url = f"{base_url}/login?reset={reset_token}"
    expiry_text = f"{expiry_days} day{'s' if expiry_days != 1 else ''}"

    content = f"""
        <h2>Reset Your Password</h2>
        <p>We received a request to reset your password. Click the button below to create a new password:</p>
        <p style="text-align: center;">
            <a href="{reset_url}" class="button">Reset Password</a>
        </p>
        <p>Or copy and paste this link into your browser:</p>
        <p style="word-break: break-all; color: #6b7280; font-size: 14px;">{reset_url}</p>
        <div class="warning">
            <strong>Security Note:</strong> This link will expire in {expiry_text}. If you didn't request a password reset, please ignore this email.
        </div>
    """

    body_text = f"""
Reset Your Password

We received a request to reset your password.

Click this link to create a new password:
{reset_url}

This link will expire in {expiry_text}. If you didn't request a password reset, please ignore this email.

- {app_name}
"""

    return await send_email(
        db=db,
        to_email=to_email,
        subject=f"Reset your {app_name} password",
        body_html=_base_template(content, app_name),
        body_text=body_text,
    )


async def send_family_invitation_email(
    db: AsyncSession,
    to_email: str,
    inviter_name: str,
    family_name: str,
    family_code: str,
    base_url: str,
) -> bool:
    """Send family invitation email with join code."""
    app_name = await get_app_name(db)
    join_url = f"{base_url}/login?join={family_code}"

    content = f"""
        <h2>You're Invited!</h2>
        <p><strong>{inviter_name}</strong> has invited you to join <strong>{family_name}</strong> on {app_name}.</p>
        <p>{app_name} helps families coordinate events, gift exchanges, potlucks, and more.</p>
        <p style="text-align: center;">
            <a href="{join_url}" class="button">Join {family_name}</a>
        </p>
        <p>Or use this family code when registering:</p>
        <p style="text-align: center;">
            <span class="code">{family_code}</span>
        </p>
        <p style="color: #6b7280; font-size: 14px;">
            If you already have an account, log in and use the family code to join.
        </p>
    """

    body_text = f"""
You're Invited!

{inviter_name} has invited you to join {family_name} on {app_name}.

{app_name} helps families coordinate events, gift exchanges, potlucks, and more.

Click this link to join:
{join_url}

Or use this family code when registering:
{family_code}

- {app_name}
"""

    return await send_email(
        db=db,
        to_email=to_email,
        subject=f"You're invited to join {family_name} on {app_name}",
        body_html=_base_template(content, app_name),
        body_text=body_text,
    )


async def send_event_cancelled_email(
    db: AsyncSession,
    to_email: str,
    recipient_name: str,
    event_title: str,
    event_date: str,
    cancellation_reason: str | None,
    cancelled_by: str,
) -> bool:
    """Send event cancellation notification."""
    app_name = await get_app_name(db)

    reason_html = ""
    reason_text = ""
    if cancellation_reason:
        reason_html = f"<p><strong>Reason:</strong> {cancellation_reason}</p>"
        reason_text = f"Reason: {cancellation_reason}"

    content = f"""
        <h2>Event Cancelled</h2>
        <p>Hi {recipient_name},</p>
        <div class="cancelled">
            <p style="margin: 0;"><strong>{event_title}</strong> scheduled for <strong>{event_date}</strong> has been cancelled.</p>
            {reason_html}
        </div>
        <p>This event was cancelled by {cancelled_by}.</p>
        <p>We apologize for any inconvenience.</p>
    """

    body_text = f"""
Event Cancelled

Hi {recipient_name},

{event_title} scheduled for {event_date} has been cancelled.
{reason_text}

This event was cancelled by {cancelled_by}.

We apologize for any inconvenience.

- {app_name}
"""

    return await send_email(
        db=db,
        to_email=to_email,
        subject=f"Event Cancelled: {event_title}",
        body_html=_base_template(content, app_name),
        body_text=body_text,
    )
