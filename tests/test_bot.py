import os
import sys
from datetime import datetime, time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

os.environ.setdefault("DISCORD_TOKEN", "test_token")
os.environ.setdefault("WISH_CHANNEL_ID", "12345")

sys.path.insert(0, "C:/Users/kashy/Documents/ChatGPT/11_11 bot")

from bot import TIMEZONE, WISH_TIMES, WishBot, get_env, get_env_int


class TestEnvHelpers:
    @patch.dict("os.environ", {"TEST_KEY": "test_value"})
    def test_get_env_exists(self):
        assert get_env("TEST_KEY") == "test_value"

    @patch.dict("os.environ", {}, clear=True)
    def test_get_env_default(self):
        assert get_env("MISSING_KEY", "default") == "default"

    @patch.dict("os.environ", {}, clear=True)
    def test_get_env_required_missing(self):
        with pytest.raises(SystemExit):
            get_env("MISSING_KEY", required=True)

    @patch.dict("os.environ", {"INT_KEY": "42"})
    def test_get_env_int_valid(self):
        assert get_env_int("INT_KEY") == 42

    @patch.dict("os.environ", {"INT_KEY": "not_an_int"})
    def test_get_env_int_invalid(self):
        with pytest.raises(SystemExit):
            get_env_int("INT_KEY")

    @patch.dict("os.environ", {}, clear=True)
    def test_get_env_int_missing_required(self):
        with pytest.raises(SystemExit):
            get_env_int("MISSING_KEY", required=True)

    @patch.dict("os.environ", {}, clear=True)
    def test_get_env_int_missing_optional(self):
        assert get_env_int("MISSING_KEY") is None


class TestWishTimes:
    def test_wish_times_length(self):
        assert len(WISH_TIMES) == 2

    def test_wish_times_values(self):
        assert WISH_TIMES[0] == time(hour=11, minute=11, tzinfo=TIMEZONE)
        assert WISH_TIMES[1] == time(hour=23, minute=11, tzinfo=TIMEZONE)

    def test_wish_times_timezone(self):
        for t in WISH_TIMES:
            assert t.tzinfo == TIMEZONE


class TestWishBot:
    @pytest.fixture
    def bot(self):
        with patch.dict("os.environ", {"DISCORD_TOKEN": "test_token", "WISH_CHANNEL_ID": "12345"}):
            bot = WishBot()
            mock_user = MagicMock()
            mock_user.id = 98765
            mock_user.name = "TestBot"
            type(bot).user = property(lambda self: mock_user)
            type(bot).guilds = property(lambda self: [])
            type(bot).latency = property(lambda self: 0.123)
            return bot

    @pytest.mark.asyncio
    async def test_on_ready_logs_info(self, bot, caplog):
        import logging
        caplog.set_level(logging.INFO, logger="wish-bot")
        # Mock the next_iteration property on the loop
        bot.send_wish_reminder._next_iteration = datetime.now(TIMEZONE)
        await bot.on_ready()
        assert "Logged in as" in caplog.text
        assert "Connected to 0 guild(s)" in caplog.text

    @pytest.mark.asyncio
    async def test_ping_command(self, bot):
        ctx = AsyncMock()
        ctx.reply = AsyncMock()
        # Test the ping command callback directly
        ping_cmd = bot.get_command("ping")
        if ping_cmd is None:
            # Commands may not be registered in test, test the function directly
            from bot import WishBot
            ping_func = WishBot.ping
            await ping_func(bot, ctx)
        else:
            await ping_cmd.callback(ctx)
        ctx.reply.assert_called_once()
        assert "123ms" in ctx.reply.call_args[0][0]

    @pytest.mark.asyncio
    async def test_next_wish_command(self, bot):
        ctx = AsyncMock()
        ctx.reply = AsyncMock()
        future_time = datetime.now(TIMEZONE)
        bot.send_wish_reminder._next_iteration = future_time
        next_wish_cmd = bot.get_command("next-wish")
        if next_wish_cmd is None:
            from bot import WishBot
            next_wish_func = WishBot.next_wish
            await next_wish_func(bot, ctx)
        else:
            await next_wish_cmd.callback(ctx)
        ctx.reply.assert_called_once()
        assert "Next wish reminder" in ctx.reply.call_args[0][0]

    @pytest.mark.asyncio
    async def test_next_wish_no_schedule(self, bot):
        ctx = AsyncMock()
        ctx.reply = AsyncMock()
        bot.send_wish_reminder._next_iteration = None
        next_wish_cmd = bot.get_command("next-wish")
        if next_wish_cmd is None:
            from bot import WishBot
            next_wish_func = WishBot.next_wish
            await next_wish_func(bot, ctx)
        else:
            await next_wish_cmd.callback(ctx)
        ctx.reply.assert_called_once_with("❌ No upcoming wish reminder scheduled.")


class TestSendWishReminder:
    @pytest.fixture
    def bot(self):
        with patch.dict("os.environ", {"DISCORD_TOKEN": "test_token", "WISH_CHANNEL_ID": "12345"}):
            bot = WishBot()
            bot.get_channel = MagicMock(return_value=None)
            bot.fetch_channel = AsyncMock()
            return bot

    @pytest.mark.asyncio
    async def test_send_wish_reminder_success(self, bot, caplog):
        import logging

        import discord
        caplog.set_level(logging.INFO, logger="wish-bot")
        channel = AsyncMock(spec=discord.TextChannel)
        channel.send = AsyncMock()
        bot.fetch_channel.return_value = channel

        await bot.send_wish_reminder()

        bot.fetch_channel.assert_called_once_with(12345)
        channel.send.assert_called_once_with("✨ It's 11:11! Make a wish, everyone! 🌟")
        assert "Sent 11:11 wish reminder" in caplog.text

    @pytest.mark.asyncio
    async def test_send_wish_reminder_channel_not_found(self, bot, caplog):
        import discord
        bot.fetch_channel.side_effect = discord.NotFound(MagicMock(), "Not Found")

        await bot.send_wish_reminder()

        assert "Channel 12345 not found" in caplog.text

    @pytest.mark.asyncio
    async def test_send_wish_reminder_forbidden(self, bot, caplog):
        import discord
        bot.fetch_channel.side_effect = discord.Forbidden(MagicMock(), "Forbidden")

        await bot.send_wish_reminder()

        assert "Missing permissions to send messages in channel 12345" in caplog.text

    @pytest.mark.asyncio
    async def test_send_wish_reminder_http_exception(self, bot, caplog):
        import discord
        bot.fetch_channel.side_effect = discord.HTTPException(MagicMock(), "Error")

        await bot.send_wish_reminder()

        assert "Failed to send wish reminder" in caplog.text
