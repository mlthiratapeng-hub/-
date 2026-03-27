import discord
from discord.ext import commands
import os
from database import init_db

# ====== KEEP ALIVE (กันหลับ) ======
from flask import Flask
from threading import Thread

app = Flask('')

@app.route('/')
def home():
    return "I'm alive"

def run():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run)
    t.start()

# ====== ตั้งค่า ======
ALLOWED_GUILD_ID = 1127935823195668480
LOG_CHANNEL_ID = 1487160190678601811

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

        # 🔥 Sync แบบ Global
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

@bot.event
async def on_app_command_completion(interaction: discord.Interaction, command):

    if not interaction.guild:
        return

    guild = interaction.guild
    channel = interaction.channel
    user = interaction.user

    embed = discord.Embed(
        title="📜 Bot Command Log",
        color=discord.Color.orange()
    )

    embed.add_field(
        name="👤 ผู้ใช้",
        value=f"{user} ({user.id})",
        inline=False
    )

    embed.add_field(
        name="🖥 เซิร์ฟเวอร์",
        value=f"{guild.name} ({guild.id})",
        inline=False
    )

    embed.add_field(
        name="🍇 ห้อง",
        value=f"{channel.mention}",
        inline=False
    )

    embed.add_field(
        name="⚙️ คำสั่ง",
        value=f"/{command.name}",
        inline=False
    )

    embed.set_footer(text="Auto Log System")

    log_channel = bot.get_channel(LOG_CHANNEL_ID)

    if log_channel:
        await log_channel.send(embed=embed)

# ====== เริ่มระบบ ======
init_db()
keep_alive()  # 🔥 เรียกกันหลับตรงนี้

bot.run(os.getenv("TOKEN"))