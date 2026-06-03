"""Regression tests: notification error logs never leak secret-bearing URLs (F10)."""

from __future__ import annotations

import logging

import httpx

from app.services.notifications.base import safe_http_error
from app.services.notifications.discord import DiscordNotificationService
from app.services.notifications.slack import SlackNotificationService
from app.services.notifications.telegram import TelegramNotificationService

SLACK_SECRET = "T00000000/B00000000/abcdefghijklmnopqrstuvwx"
DISCORD_SECRET = "123456789012345678/aZ_secret-webhook-token"
TELEGRAM_TOKEN = "123456789:AAEseCReT_bot_TOKEN_value"


def _status_error(url: str, status: int) -> httpx.HTTPStatusError:
    request = httpx.Request("POST", url)
    response = httpx.Response(status, request=request)
    return httpx.HTTPStatusError("boom", request=request, response=response)


class TestSafeHttpError:
    def test_keeps_status_and_host_drops_secret_path(self):
        out = safe_http_error(
            _status_error(f"https://hooks.slack.com/services/{SLACK_SECRET}", 404)
        )
        assert SLACK_SECRET not in out
        assert "hooks.slack.com" in out
        assert "404" in out

    def test_telegram_token_in_path_not_leaked(self):
        out = safe_http_error(
            _status_error(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", 401)
        )
        assert TELEGRAM_TOKEN not in out
        assert "api.telegram.org" in out

    def test_non_http_error_falls_back_to_type_name(self):
        out = safe_http_error(ValueError("bad json"))
        assert "ValueError" in out
        assert "bad json" not in out


def _mock_client(status: int) -> httpx.AsyncClient:
    return httpx.AsyncClient(transport=httpx.MockTransport(lambda req: httpx.Response(status)))


class TestChannelSendDoesNotLogSecret:
    async def test_slack(self, caplog):
        svc = SlackNotificationService(
            webhook_url=f"https://hooks.slack.com/services/{SLACK_SECRET}"
        )
        svc.client = _mock_client(404)
        with caplog.at_level(logging.ERROR):
            result = await svc.send(title="t", message="m")
        await svc.close()
        assert result is False
        assert SLACK_SECRET not in caplog.text

    async def test_discord(self, caplog):
        svc = DiscordNotificationService(
            webhook_url=f"https://discord.com/api/webhooks/{DISCORD_SECRET}"
        )
        svc.client = _mock_client(404)
        with caplog.at_level(logging.ERROR):
            result = await svc.send(title="t", message="m")
        await svc.close()
        assert result is False
        assert DISCORD_SECRET not in caplog.text

    async def test_telegram(self, caplog):
        svc = TelegramNotificationService(bot_token=TELEGRAM_TOKEN, chat_id="42")
        svc.client = _mock_client(401)
        with caplog.at_level(logging.ERROR):
            result = await svc.send(title="t", message="m")
        await svc.close()
        assert result is False
        assert TELEGRAM_TOKEN not in caplog.text


class TestTestConnectionDoesNotLeakSecret:
    async def test_telegram_connection_test_message_omits_token(self):
        """The (success, message) returned to the API must not carry the bot token."""

        def boom(request: httpx.Request) -> httpx.Response:
            raise httpx.ConnectError("unreachable", request=request)

        svc = TelegramNotificationService(bot_token=TELEGRAM_TOKEN, chat_id="42")
        svc.client = httpx.AsyncClient(transport=httpx.MockTransport(boom))
        ok, message = await svc.test_connection()
        await svc.close()
        assert ok is False
        assert TELEGRAM_TOKEN not in message
