import discord
from discord.ext import commands
from discord import app_commands
import os
from dotenv import load_dotenv
from gtts import gTTS
import yt_dlp

# =========================
# LOAD TOKEN
# =========================
load_dotenv()
TOKEN = os.getenv("TOKEN")

# =========================
# INTENTS
# =========================
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# =========================
# JOIN
# =========================
@bot.tree.command(name="join", description="ให้บอทเข้าห้องเสียงและเปิดโหมดอ่านแชท")
async def join(interaction: discord.Interaction):
    if interaction.user.voice:
        channel = interaction.user.voice.channel
        if interaction.guild.voice_client is None:
            await channel.connect()
        await interaction.response.send_message("เข้าห้องแล้ว พร้อมอ่านแชท ✅")
    else:
        await interaction.response.send_message("คุณต้องอยู่ในห้องเสียงก่อน ❌")

# =========================
# LEAVE
# =========================
@bot.tree.command(name="leave", description="ออกจากห้องเสียง")
async def leave(interaction: discord.Interaction):
    if interaction.guild.voice_client:
        await interaction.guild.voice_client.disconnect()
        await interaction.response.send_message("ออกจากห้องเสียงแล้ว ⏹️")
    else:
        await interaction.response.send_message("บอทไม่ได้อยู่ในห้อง ❌")

# =========================
# PLAY MUSIC
# =========================
@bot.tree.command(name="play", description="เปิดเพลงจาก YouTube")
@app_commands.describe(query="ชื่อเพลงหรือ URL")
async def play(interaction: discord.Interaction, query: str):

    if not interaction.guild.voice_client:
        await interaction.response.send_message("บอทยังไม่เข้าห้องเสียง ❌")
        return

    await interaction.response.send_message(f"กำลังเปิด: {query} 🎵")

    ydl_opts = {
        "format": "bestaudio",
        "quiet": True
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(f"ytsearch:{query}", download=False)
        url = info["entries"][0]["url"]

    source = await discord.FFmpegOpusAudio.from_probe(url)
    interaction.guild.voice_client.play(source)

# =========================
# AUTO TTS (อ่านข้อความอัตโนมัติ)
# =========================
@bot.event
async def on_message(message):
    if message.author.bot:
        return

    if message.guild and message.guild.voice_client:
        vc = message.guild.voice_client

        if not vc.is_playing():
            try:
                tts = gTTS(text=message.content, lang="th")
                tts.save("tts.mp3")

                source = discord.FFmpegPCMAudio("tts.mp3")
                vc.play(source)
            except Exception as e:
                print("TTS Error:", e)

    await bot.process_commands(message)

# =========================
# READY
# =========================
@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"Logged in as {bot.user}")

# =========================
# RUN
# =========================
bot.run(TOKEN)