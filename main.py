import discord
from discord.ext import commands
import os
from database import init_db

# ====== ตั้งค่า ======
ALLOWED_GUILD_ID = 1476624073990738022  # (ยังเก็บไว้ เผื่อใช้ใน cog)

intents = discord.Intents.all()

class MyBot(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix="!",
            intents=intents
        )

    async def setup_hook(self):
        # โหลดทุก cog
        for file in os.listdir("./cogs"):
            if file.endswith(".py"):
                await self.load_extension(f"cogs.{file[:-3]}")
                print(f"Loaded {file}")

        # 🔥 Sync แบบ Global (ทุกเซิร์ฟ)
        synced = await self.tree.sync()
        print(f"Synced {len(synced)} global commands")

bot = MyBot()

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")

@bot.event
async def on_message(message):
    if message.author.bot:
        return
    await bot.process_commands(message)

# เริ่มระบบฐานข้อมูล
init_db()

bot.run(os.getenv("TOKEN"))