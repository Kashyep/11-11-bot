import os
from datetime import time
from zoneinfo import ZoneInfo

import discord
from discord.ext import commands, tasks
from dotenv import load_dotenv


load_dotenv()

TOKEN = os.environ["DISCORD_TOKEN"]
CHANNEL_ID = int(os.environ["WISH_CHANNEL_ID"])
TIMEZONE = ZoneInfo(os.getenv("TIMEZONE", "Asia/Kolkata"))

WISH_TIMES = [
    time(hour=11, minute=11, tzinfo=TIMEZONE),
    time(hour=23, minute=11, tzinfo=TIMEZONE),
]

intents = discord.Intents.default()


class WishBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        self.send_wish_reminder.start()

    @tasks.loop(time=WISH_TIMES)
    async def send_wish_reminder(self):
        channel = self.get_channel(CHANNEL_ID)

        if channel is None:
            channel = await self.fetch_channel(CHANNEL_ID)

        await channel.send("✨ It’s 11:11! Make a wish, everyone! 🌟")

    @send_wish_reminder.before_loop
    async def before_reminder(self):
        await self.wait_until_ready()


bot = WishBot()
bot.run(TOKEN)

