import discord
from discord.ext import commands
import os
from database import init_db

# ====== ตั้งค่า ======
ALLOWED_GUILD_ID = 1476624073990738022

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
                try:
                    await self.load_extension(f"cogs.{file[:-3]}")
                    print(f"Loaded {file}")
                except Exception as e:
                    print(f"Failed to load {file}: {e}")

        await self.wait_until_ready()

        try:
            # 🔥 Sync Guild ก่อน (ขึ้นทันที)
            guild = discord.Object(id=ALLOWED_GUILD_ID)
            guild_synced = await self.tree.sync(guild=guild)
            print(f"Synced {len(guild_synced)} guild commands")

            # 🔥 Sync Global ด้วย (ให้ใช้ได้ทุกเซิฟ)
            global_synced = await self.tree.sync()
            print(f"Synced {len(global_synced)} global commands")

        except Exception as e:
            print(f"Sync error: {e}")


bot = MyBot()


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} ({bot.user.id})")


@bot.event
async def on_message(message):
    if message.author.bot:
        return
    await bot.process_commands(message)


# เริ่มระบบ
init_db()

bot.run(os.getenv("TOKEN"))