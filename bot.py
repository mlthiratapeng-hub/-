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
loop_mode = {}
volume_level = {}
speed_level = {}

# ================= READY =================
@bot.event
async def on_ready():
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} commands globally")
    except Exception as e:
        print(e)
    print(f"Logged in as {bot.user}")

# ================= JOIN =================
@bot.tree.command(name="join", description="เข้าห้องเสียง")
async def join(interaction: discord.Interaction):
    if interaction.user.voice:
        channel = interaction.user.voice.channel
        if not interaction.guild.voice_client:
            await channel.connect()

        embed = discord.Embed(
            title="🎧 Joined",
            description="บอทเข้าห้องเสียงแล้ว",
            color=0x2ecc71
        )
        await interaction.response.send_message(embed=embed)
    else:
        await interaction.response.send_message("คุณต้องอยู่ในห้องเสียงก่อน ❌")

# ================= LEAVE =================
@bot.tree.command(name="leave", description="ออกจากห้องเสียง")
async def leave(interaction: discord.Interaction):
    if interaction.guild.voice_client:
        await interaction.guild.voice_client.disconnect()
        await interaction.response.send_message("ออกจากห้องแล้ว 👋")
    else:
        await interaction.response.send_message("บอทไม่ได้อยู่ในห้อง ❌")

# ================= PLAY =================
@bot.tree.command(name="play", description="เปิดเพลงจากชื่อเพลง")
@app_commands.describe(query="ชื่อเพลง")
async def play(interaction: discord.Interaction, query: str):

    if not interaction.guild.voice_client:
        await interaction.response.send_message("บอทยังไม่เข้าห้องเสียง ❌")
        return

    guild_id = interaction.guild.id
    if guild_id not in queues:
        queues[guild_id] = []

    ydl_opts = {"format": "bestaudio", "quiet": True}

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(f"ytsearch:{query}", download=False)
        data = info["entries"][0]

    queues[guild_id].append(data)

    embed = discord.Embed(
        title="🎵 Added to Queue",
        description=data["title"],
        color=0x3498db
    )
    await interaction.response.send_message(embed=embed)

    if not interaction.guild.voice_client.is_playing():
        await play_next(interaction.guild)

# ================= PLAY NEXT =================
async def play_next(guild):
    guild_id = guild.id
    vc = guild.voice_client

    if not queues.get(guild_id):
        return

    data = queues[guild_id][0]

    volume = volume_level.get(guild_id, 1.0)
    speed = speed_level.get(guild_id, 1.0)

    ffmpeg_options = {
        "options": f"-filter:a atempo={speed}"
    }

    source = discord.PCMVolumeTransformer(
        discord.FFmpegPCMAudio(data["url"], **ffmpeg_options),
        volume=volume
    )

    def after_playing(error):
        if loop_mode.get(guild_id, False):
            vc.play(source, after=after_playing)
        else:
            queues[guild_id].pop(0)
            if queues[guild_id]:
                bot.loop.create_task(play_next(guild))

    vc.play(source, after=after_playing)

# ================= SKIP =================
@bot.tree.command(name="skip", description="ข้ามเพลง")
async def skip(interaction: discord.Interaction):
    if interaction.guild.voice_client:
        interaction.guild.voice_client.stop()
        await interaction.response.send_message("⏭️ ข้ามแล้ว")

# ================= LOOP =================
@bot.tree.command(name="loop", description="เปิด/ปิด loop")
async def loop(interaction: discord.Interaction):
    guild_id = interaction.guild.id
    loop_mode[guild_id] = not loop_mode.get(guild_id, False)
    await interaction.response.send_message(f"🔁 Loop: {loop_mode[guild_id]}")

# ================= QUEUE =================
@bot.tree.command(name="queue", description="ดูคิวเพลง")
async def queue(interaction: discord.Interaction):
    guild_id = interaction.guild.id
    if not queues.get(guild_id):
        await interaction.response.send_message("ไม่มีเพลงในคิว ❌")
        return

    description = "\n".join(
        [f"{i+1}. {song['title']}" for i, song in enumerate(queues[guild_id])]
    )

    embed = discord.Embed(
        title="📜 Music Queue",
        description=description,
        color=0xf1c40f
    )
    await interaction.response.send_message(embed=embed)

# ================= VOLUME =================
@bot.tree.command(name="volume", description="ปรับเสียง 1-1000")
@app_commands.describe(level="1-1000")
async def volume(interaction: discord.Interaction, level: int):
    guild_id = interaction.guild.id
    volume_level[guild_id] = level / 100
    await interaction.response.send_message(f"🔊 Volume: {level}")

# ================= SPEED =================
@bot.tree.command(name="speed", description="ปรับความเร็ว 0.5 - 2.0")
@app_commands.describe(rate="0.5 - 2.0")
async def speed(interaction: discord.Interaction, rate: float):
    guild_id = interaction.guild.id
    speed_level[guild_id] = rate
    await interaction.response.send_message(f"⚡ Speed: {rate}")

bot.run(TOKEN)