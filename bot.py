import discord
from discord.ext import commands
from discord import app_commands
import yt_dlp
import os
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("TOKEN")

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

queues = {}
loop_status = {}
volume_levels = {}
speed_levels = {}

# =========================
# JOIN
# =========================
@bot.tree.command(name="join")
async def join(interaction: discord.Interaction):
    if interaction.user.voice:
        channel = interaction.user.voice.channel
        if not interaction.guild.voice_client:
            await channel.connect()

        embed = discord.Embed(
            title="🎧 Joined Voice",
            description="บอทเข้าห้องแล้ว",
            color=0x2ecc71
        )
        await interaction.response.send_message(embed=embed)
    else:
        await interaction.response.send_message("คุณต้องอยู่ในห้องเสียงก่อน ❌")

# =========================
# PLAY
# =========================
@bot.tree.command(name="play")
@app_commands.describe(query="ชื่อเพลง")
async def play(interaction: discord.Interaction, query: str):

    if not interaction.guild.voice_client:
        await interaction.response.send_message("บอทยังไม่เข้าห้องเสียง ❌")
        return

    guild_id = interaction.guild.id

    if guild_id not in queues:
        queues[guild_id] = []

    ydl_opts = {
        "format": "bestaudio",
        "quiet": True
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(f"ytsearch:{query}", download=False)
        data = info["entries"][0]

    queues[guild_id].append(data)

    embed = discord.Embed(
        title="🎵 เพิ่มเพลงเข้าคิว",
        description=f"{data['title']}",
        color=0x3498db
    )

    await interaction.response.send_message(embed=embed)

    if not interaction.guild.voice_client.is_playing():
        await play_next(interaction.guild)

# =========================
# PLAY NEXT
# =========================
async def play_next(guild):

    guild_id = guild.id
    vc = guild.voice_client

    if guild_id not in queues or not queues[guild_id]:
        return

    data = queues[guild_id][0]

    volume = volume_levels.get(guild_id, 1.0)
    speed = speed_levels.get(guild_id, 1.0)

    ffmpeg_options = {
        "options": f"-filter:a \"atempo={speed},volume={volume}\""
    }

    source = await discord.FFmpegOpusAudio.from_probe(data["url"], **ffmpeg_options)

    def after_playing(error):
        if loop_status.get(guild_id, False):
            vc.play(source, after=after_playing)
        else:
            queues[guild_id].pop(0)
            if queues[guild_id]:
                bot.loop.create_task(play_next(guild))

    vc.play(source, after=after_playing)

# =========================
# SKIP
# =========================
@bot.tree.command(name="skip")
async def skip(interaction: discord.Interaction):
    if interaction.guild.voice_client:
        interaction.guild.voice_client.stop()
        await interaction.response.send_message("⏭️ ข้ามเพลงแล้ว")

# =========================
# LOOP
# =========================
@bot.tree.command(name="loop")
async def loop(interaction: discord.Interaction):
    guild_id = interaction.guild.id
    loop_status[guild_id] = not loop_status.get(guild_id, False)
    await interaction.response.send_message(f"🔁 Loop: {loop_status[guild_id]}")

# =========================
# VOLUME
# =========================
@bot.tree.command(name="volume")
@app_commands.describe(level="1-1000")
async def volume(interaction: discord.Interaction, level: int):
    guild_id = interaction.guild.id
    volume_levels[guild_id] = level / 100
    await interaction.response.send_message(f"🔊 Volume set to {level}")

# =========================
# SPEED
# =========================
@bot.tree.command(name="speed")
@app_commands.describe(rate="0.5 - 2.0")
async def speed(interaction: discord.Interaction, rate: float):
    guild_id = interaction.guild.id
    speed_levels[guild_id] = rate
    await interaction.response.send_message(f"⚡ Speed set to {rate}")

# =========================
# READY
# =========================
@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"Logged in as {bot.user}")

bot.run(TOKEN)