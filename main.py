import discord
from discord.ext import commands
import os
from database import init_db

intents = discord.Intents.all()

class MyBot(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix="!",
            intents=intents
        )

    async def setup_hook(self):
        # โหลดทุกไฟล์ในโฟลเดอร์ cogs
        for file in os.listdir("./cogs"):
            if file.endswith(".py"):
                await self.load_extension(f"cogs.{file[:-3]}")
                print(f"Loaded {file}")

bot = MyBot()

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    await bot.tree.sync()
    print("Slash synced")

init_db()

bot.run(os.getenv("TOKEN"))