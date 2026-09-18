import logging
import os
import sys
from datetime import datetime, time
from zoneinfo import ZoneInfo

import discord
from discord.ext import commands, tasks
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[logging.StreamHandler(sys.stdout)],
)
log = logging.getLogger("wish-bot")

def get_env(key: str, default: str | None = None, required: bool = False) -> str:
    value = os.getenv(key, default)
    if required and value is None:
        log.critical("Missing required environment variable: %s", key)
        sys.exit(1)
    return value

def get_env_int(key: str, required: bool = False) -> int | None:
    value = get_env(key, required=required)
    if value is None:
        return None
    try:
        return int(value)
    except ValueError:
        log.critical("Environment variable %s must be an integer, got: %s", key, value)
        sys.exit(1)

TOKEN = get_env("DISCORD_TOKEN", required=True)
CHANNEL_ID = get_env_int("WISH_CHANNEL_ID", required=True)
TIMEZONE_STR = get_env("TIMEZONE", "Asia/Kolkata")
try:
    TIMEZONE = ZoneInfo(TIMEZONE_STR)
except Exception as e:
    log.critical("Invalid TIMEZONE '%s': %s", TIMEZONE_STR, e)
    sys.exit(1)

WISH_TIMES = [
    time(hour=11, minute=11, tzinfo=TIMEZONE),
    time(hour=23, minute=11, tzinfo=TIMEZONE),
]

intents = discord.Intents.default()
intents.message_content = True


class WishBot(commands.Bot):
    def __init__(self) -> None:
        super().__init__(command_prefix="!", intents=intents, help_command=None)

    async def setup_hook(self) -> None:
        log.info("Starting wish reminder task")
        self.send_wish_reminder.start()

    @tasks.loop(time=WISH_TIMES)
    async def send_wish_reminder(self) -> None:
        try:
            channel = self.get_channel(CHANNEL_ID)
            if channel is None:
                log.info("Channel not in cache, fetching...")
                channel = await self.fetch_channel(CHANNEL_ID)

            messageable_types = (
                discord.TextChannel
                | discord.Thread
                | discord.VoiceChannel
                | discord.StageChannel
            )
            if not isinstance(channel, messageable_types):
                log.error(
                    "Channel %s is not a messageable channel type: %s",
                    CHANNEL_ID,
                    type(channel).__name__,
                )
                return

            await channel.send("✨ It's 11:11! Make a wish, everyone! 🌟")
            log.info("Sent 11:11 wish reminder to channel %s", CHANNEL_ID)

        except discord.NotFound:
            log.error("Channel %s not found", CHANNEL_ID)
        except discord.Forbidden:
            log.error("Missing permissions to send messages in channel %s", CHANNEL_ID)
        except discord.HTTPException as e:
            log.error("Failed to send wish reminder: %s", e)
        except Exception as e:
            log.exception("Unexpected error in send_wish_reminder: %s", e)

    @send_wish_reminder.before_loop
    async def before_reminder(self) -> None:
        await self.wait_until_ready()
        log.info("Wish reminder task ready")

    async def on_ready(self) -> None:
        log.info("Logged in as %s (ID: %s)", self.user, self.user.id)
        log.info("Connected to %d guild(s)", len(self.guilds))
        next_run = self.send_wish_reminder.next_iteration
        if next_run:
            next_run_str = next_run.astimezone(TIMEZONE).strftime("%Y-%m-%d %H:%M:%S %Z")
            log.info("Next wish reminder scheduled for: %s", next_run_str)

    @commands.command(name="ping")
    async def ping(self, ctx: commands.Context) -> None:
        """Check bot latency."""
        latency = round(self.latency * 1000)
        await ctx.reply(f"🏓 Pong! Latency: {latency}ms")

    @commands.command(name="test-wish", aliases=["testwish"])
    @commands.has_permissions(manage_messages=True)
    async def test_wish(self, ctx: commands.Context) -> None:
        """Manually trigger a wish reminder (requires Manage Messages)."""
        try:
            await ctx.send("✨ It's 11:11! Make a wish, everyone! 🌟")
            await ctx.message.add_reaction("✅")
        except discord.Forbidden:
            await ctx.reply("❌ I don't have permission to send messages here.")
        except Exception as e:
            log.exception("Error in test-wish: %s", e)
            await ctx.reply(f"❌ Error: {e}")

    @commands.command(name="next-wish", aliases=["nextwish"])
    async def next_wish(self, ctx: commands.Context) -> None:
        """Show when the next wish reminder will be sent."""
        next_run = self.send_wish_reminder.next_iteration
        if next_run:
            next_run_local = next_run.astimezone(TIMEZONE)
            now = datetime.now(TIMEZONE)
            diff = next_run_local - now
            hours, remainder = divmod(int(diff.total_seconds()), 3600)
            minutes, _ = divmod(remainder, 60)
            await ctx.reply(
                f"🕐 Next wish reminder: **{next_run_local.strftime('%Y-%m-%d %H:%M:%S %Z')}** "
                f"(in {hours}h {minutes}m)"
            )
        else:
            await ctx.reply("❌ No upcoming wish reminder scheduled.")


bot = WishBot()

if __name__ == "__main__":
    try:
        bot.run(TOKEN, log_handler=None)
    except KeyboardInterrupt:
        log.info("Bot stopped by user")
    except discord.LoginFailure:
        log.critical("Invalid DISCORD_TOKEN")
        sys.exit(1)
    except Exception as e:
        log.critical("Fatal error: %s", e)
        sys.exit(1)

