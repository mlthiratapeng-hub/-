import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
from gtts import gTTS

load_dotenv()
TOKEN = os.getenv("TOKEN")

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
        await interaction.response.send_message("ออกจากห้องเสียงแล้ว 🎚️")
    else:
        await interaction.response.send_message("บอทไม่ได้อยู่ในห้อง ❌")

# =========================
# AUTO TTS
# =========================
@bot.event
async def on_message(message):
    if message.author.bot:
        return

    if message.guild and message.guild.voice_client:
        vc = message.guild.voice_client

        if not vc.is_playing():
            tts = gTTS(text=message.content, lang="th")
            tts.save("tts.mp3")

            source = discord.FFmpegPCMAudio("tts.mp3")
            vc.play(source)

    await bot.process_commands(message)

# =========================
# READY
# =========================
@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"Logged in as {bot.user}")

bot.run(BOTTOKEN)