"""Tests for the background notification helper (fire.py).

Verifies:
- send_notification_background creates its own session
- Exceptions are caught and logged, never propagated
- The correct dispatcher method is called with the right kwargs
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

from app.services.notifications.fire import send_notification_background


class TestSendNotificationBackground:
    async def test_calls_dispatcher_method_with_kwargs(self):
        """Verify the correct dispatcher method is called with forwarded kwargs."""
        mock_dispatcher = MagicMock()
        mock_method = AsyncMock(return_value={"ntfy": True})
        mock_dispatcher.notify_event_created = mock_method

        mock_session = AsyncMock()
        mock_session_ctx = AsyncMock()
        mock_session_ctx.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session_ctx.__aexit__ = AsyncMock(return_value=False)

        with (
            patch(
                "app.services.notifications.fire.async_session_maker",
                return_value=mock_session_ctx,
            ),
            patch(
                "app.services.notifications.fire.NotificationDispatcher",
                return_value=mock_dispatcher,
            ),
        ):
            await send_notification_background(
                "notify_event_created",
                event_title="Test Event",
                family_name="Test Family",
                creator_name="Alice",
                event_date="March 14, 2026",
            )

        mock_method.assert_called_once_with(
            event_title="Test Event",
            family_name="Test Family",
            creator_name="Alice",
            event_date="March 14, 2026",
        )

    async def test_creates_own_session(self):
        """Verify async_session_maker is called to create a fresh session."""
        mock_dispatcher = MagicMock()
        mock_dispatcher.notify_event_created = AsyncMock(return_value={})

        mock_session = AsyncMock()
        mock_session_ctx = AsyncMock()
        mock_session_ctx.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session_ctx.__aexit__ = AsyncMock(return_value=False)
        mock_factory = MagicMock(return_value=mock_session_ctx)

        with (
            patch(
                "app.services.notifications.fire.async_session_maker",
                mock_factory,
            ),
            patch(
                "app.services.notifications.fire.NotificationDispatcher",
                return_value=mock_dispatcher,
            ) as mock_dispatcher_cls,
        ):
            await send_notification_background(
                "notify_event_created",
                event_title="X",
                family_name="Y",
                creator_name="Z",
                event_date="A",
            )

        # Session factory was called
        mock_factory.assert_called_once()
        # Dispatcher was instantiated with the session from the factory
        mock_dispatcher_cls.assert_called_once_with(mock_session)

    async def test_exception_is_caught_and_logged(self):
        """Verify exceptions don't propagate — they're logged instead."""
        mock_dispatcher = MagicMock()
        mock_dispatcher.notify_event_created = AsyncMock(side_effect=RuntimeError("SMTP down"))

        mock_session = AsyncMock()
        mock_session_ctx = AsyncMock()
        mock_session_ctx.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session_ctx.__aexit__ = AsyncMock(return_value=False)

        with (
            patch(
                "app.services.notifications.fire.async_session_maker",
                return_value=mock_session_ctx,
            ),
            patch(
                "app.services.notifications.fire.NotificationDispatcher",
                return_value=mock_dispatcher,
            ),
            patch("app.services.notifications.fire.logger") as mock_logger,
        ):
            # Should NOT raise
            await send_notification_background(
                "notify_event_created",
                event_title="Broken",
                family_name="Family",
                creator_name="Bob",
                event_date="Tomorrow",
            )

        # Error was logged
        mock_logger.error.assert_called_once()
        assert "notify_event_created" in mock_logger.error.call_args[0][1]

    async def test_notify_family_member_joined_callable(self):
        """Verify notify_family_member_joined can be dispatched through the helper."""
        mock_dispatcher = MagicMock()
        mock_method = AsyncMock(return_value={})
        mock_dispatcher.notify_family_member_joined = mock_method

        mock_session = AsyncMock()
        mock_session_ctx = AsyncMock()
        mock_session_ctx.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session_ctx.__aexit__ = AsyncMock(return_value=False)

        with (
            patch(
                "app.services.notifications.fire.async_session_maker",
                return_value=mock_session_ctx,
            ),
            patch(
                "app.services.notifications.fire.NotificationDispatcher",
                return_value=mock_dispatcher,
            ),
        ):
            await send_notification_background(
                "notify_family_member_joined",
                member_name="Charlie",
                family_name="Smith Family",
            )

        mock_method.assert_called_once_with(
            member_name="Charlie",
            family_name="Smith Family",
        )

    async def test_invalid_method_name_caught(self):
        """Verify calling a nonexistent method is caught, not raised."""
        mock_dispatcher = MagicMock(spec=[])  # No methods

        mock_session = AsyncMock()
        mock_session_ctx = AsyncMock()
        mock_session_ctx.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session_ctx.__aexit__ = AsyncMock(return_value=False)

        with (
            patch(
                "app.services.notifications.fire.async_session_maker",
                return_value=mock_session_ctx,
            ),
            patch(
                "app.services.notifications.fire.NotificationDispatcher",
                return_value=mock_dispatcher,
            ),
            patch("app.services.notifications.fire.logger") as mock_logger,
        ):
            # Should NOT raise despite invalid method
            await send_notification_background(
                "notify_nonexistent",
                some_arg="value",
            )

        mock_logger.error.assert_called_once()
