import discord
from discord.ext import commands
import os
from database import init_db

# ====== ตั้งค่า ======
ALLOWED_GUILD_ID = 1476624073990738022  # 🔥 ใส่ไอดีเซิร์ฟจริงของคุณ

# 🔥 แก้ตรงนี้
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

        # 🔥 สำคัญมาก: Sync แบบ Guild เท่านั้น
        guild = discord.Object(id=ALLOWED_GUILD_ID)
        synced = await self.tree.sync(guild=guild)
        print(f"Synced {len(synced)} commands to guild")


bot = MyBot()


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")


@bot.event
async def on_message(message):
    if message.author.bot:
        return
    await bot.process_commands(message)


# เริ่มระบบ
init_db()

bot.run(os.getenv("TOKEN"))