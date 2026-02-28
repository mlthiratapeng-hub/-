import discord
from discord.ext import commands
import os
from database import init_db

intents = discord.Intents.default()
intents.message_content = True  # สำคัญมากสำหรับ !command

class MyBot(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix="!",
            intents=intents
        )

    async def setup_hook(self):
        for file in os.listdir("./cogs"):
            if file.endswith(".py"):
                await self.load_extension(f"cogs.{file[:-3]}")
                print(f"Loaded {file}")

bot = MyBot()

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    try:
        synced = await bot.tree.sync()
        print(f"Slash synced {len(synced)} commands")
    except Exception as e:
        print(e)

# ถ้าอยากดูว่าบอทอ่านข้อความไหม เปิดอันนี้
@bot.event
async def on_message(message):
    if message.author.bot:
        return
    print("Message received:", message.content)
    await bot.process_commands(message)

init_db()

bot.run(os.getenv("TOKEN"))