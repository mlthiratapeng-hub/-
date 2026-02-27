import discord
from discord import app_commands
from discord.ext import commands
import yt_dlp
import asyncio
import os
import random
from urllib.parse import urlparse
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("TOKEN")

PROMO_IMAGE = "https://cdn.discordapp.com/attachments/1476624074921738467/1476892902880706691/77a78e76e8b70493bb8615f5b06e36f7.gif"

LINK_CHANNEL_ID = 1476914330854490204
REQUIRED_GUILD_ID = 1476624073990738022

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

song_queues = {}
verification_data = {}

# ================= EMBED =================

def promo_embed(title, desc):
    embed = discord.Embed(title=title, description=desc, color=0x2f3136)
    embed.set_image(url=PROMO_IMAGE)
    return embed

# ================= MUSIC SYSTEM =================

async def play_next(guild):
    if guild.id in song_queues and song_queues[guild.id]:
        url, title = song_queues[guild.id].pop(0)
        vc = guild.voice_client
        if vc:
            source = await discord.FFmpegOpusAudio.from_probe(url, options='-vn')
            vc.play(
                source,
                after=lambda e: asyncio.run_coroutine_threadsafe(
                    play_next(guild), bot.loop
                )
            )

@bot.tree.command(name="join", description="🍗 ให้บอทเข้าห้องเสียงของคุณ")
async def join(interaction: discord.Interaction):
    await interaction.response.defer()

    if not interaction.user.voice:
        return await interaction.followup.send(embed=promo_embed("🦞ผิดพลาด", "🥢ต้องอยู่ในห้องเสียงก่อน"))

    if interaction.guild.voice_client:
        return await interaction.followup.send(embed=promo_embed("🍍แจ้งเตือน", "🍋บอทอยู่ในห้องแล้ว"))

    await interaction.user.voice.channel.connect()
    await interaction.followup.send(embed=promo_embed("🍏สำเร็จ", "🥑บอทเข้าห้องเสียงแล้ว"))

@bot.tree.command(name="leave", description="🍲 ให้บอทออกจากห้องเสียง")
async def leave(interaction: discord.Interaction):
    await interaction.response.defer()
    vc = interaction.guild.voice_client

    if vc:
        await vc.disconnect()
        await interaction.followup.send(embed=promo_embed("🧀ออกแล้ว", "🥯บอทออกจากห้องเสียงแล้ว"))
    else:
        await interaction.followup.send(embed=promo_embed("🍒ผิดพลาด", "🌰บอทไม่ได้อยู่ในห้องเสียง"))

@bot.tree.command(name="play", description="🫛 เล่นเพลงจาก YouTube")
@app_commands.describe(query="ชื่อเพลงหรือ URL")
async def play(interaction: discord.Interaction, query: str):
    await interaction.response.defer(thinking=True)

    if not interaction.user.voice:
        return await interaction.followup.send(embed=promo_embed("ผิดพลาด", "ต้องอยู่ในห้องเสียงก่อน"))

    if not interaction.guild.voice_client:
        await interaction.user.voice.channel.connect()

    vc = interaction.guild.voice_client

    YDL_OPTIONS = {'format': 'bestaudio'}
    with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl:
        info = ydl.extract_info(f"ytsearch:{query}", download=False)
        url = info['entries'][0]['url']
        title = info['entries'][0]['title']

    if interaction.guild.id not in song_queues:
        song_queues[interaction.guild.id] = []

    song_queues[interaction.guild.id].append((url, title))

    if not vc.is_playing():
        await play_next(interaction.guild)

    await interaction.followup.send(embed=promo_embed("🍊 เพิ่มเพลงแล้ว", f"**{title}**"))

@bot.tree.command(name="queue", description="📜 ดูรายการเพลงในคิว")
async def queue(interaction: discord.Interaction):
    await interaction.response.defer()

    if interaction.guild.id not in song_queues or not song_queues[interaction.guild.id]:
        return await interaction.followup.send(embed=promo_embed("คิวว่าง", "ไม่มีเพลงในคิว"))

    desc = ""
    for i, (_, title) in enumerate(song_queues[interaction.guild.id], start=1):
        desc += f"{i}. {title}\n"

    await interaction.followup.send(embed=promo_embed("📜 คิวเพลง", desc))

@bot.tree.command(name="skip", description="⏭️ ข้ามเพลงปัจจุบัน")
async def skip(interaction: discord.Interaction):
    await interaction.response.defer()
    vc = interaction.guild.voice_client

    if not vc or not vc.is_playing():
        return await interaction.followup.send(embed=promo_embed("🍎ผิดพลาด", "🍓ไม่มีเพลงกำลังเล่น"))

    vc.stop()
    await interaction.followup.send(embed=promo_embed("⏭️ ข้ามแล้ว", "เพลงถูกข้ามเรียบร้อย"))

@bot.tree.command(name="clearqueue", description="🗑️ ล้างคิวเพลงทั้งหมด")
async def clearqueue(interaction: discord.Interaction):
    await interaction.response.defer()

    if interaction.guild.id in song_queues:
        song_queues[interaction.guild.id].clear()

    await interaction.followup.send(embed=promo_embed("🗑️ ล้างคิวแล้ว", "คิวเพลงถูกล้างทั้งหมด"))

@bot.tree.command(name="stop", description="⏸️ หยุดเพลงชั่วคราวตามเวลาที่กำหนด")
@app_commands.describe(time="จำนวนวินาทีที่ต้องการหยุด")
async def stop(interaction: discord.Interaction, time: int):
    await interaction.response.defer()

    vc = interaction.guild.voice_client

    if not vc or not vc.is_playing():
        return await interaction.followup.send(embed=promo_embed("🥩ผิดพลาด", "🥓ไม่มีเพลงกำลังเล่น"))

    vc.pause()
    await interaction.followup.send(embed=promo_embed("⏸️ หยุดแล้ว", f"พักเพลง {time} วินาที"))

    await asyncio.sleep(time)

    if vc.is_paused():
        vc.resume()
        await interaction.channel.send(embed=promo_embed("▶️ เล่นต่อ", "🧇เพลงเล่นต่ออัตโนมัติแล้ว"))

# ================= VASVEX =================

@bot.tree.command(name="vasvex", description="🔐 สร้างระบบยืนยันตัวตน")
@app_commands.describe(
    channel="🌭ห้องที่จะส่ง",
    role="🥪ยศที่จะให้",
    image_url="🍞ลิ้งรูป (ไม่ใส่ก็ได้)"
)
async def vasvex(interaction: discord.Interaction,
                 channel: discord.TextChannel,
                 role: discord.Role,
                 image_url: str = None):

    # ✅ ต้องเป็นแอดมินในเซิร์ฟที่กดใช้
    if not interaction.user.guild_permissions.administrator:
        return await interaction.response.send_message(
            "🍁ต้องเป็นแอดมินในเซิร์ฟนี้ก่อน",
            ephemeral=True
        )

    # ✅ ต้องอยู่ในเซิร์ฟ REQUIRED_GUILD_ID
    required_guild = bot.get_guild(REQUIRED_GUILD_ID)
    if not required_guild:
        return await interaction.response.send_message(
            "🍄ในไม่พบเซิร์ฟเวอร์ที่กำหนด",
            ephemeral=True
        )

    member = required_guild.get_member(interaction.user.id)
    if not member:
        return await interaction.response.send_message(
            "🪻ต้องเข้าดิสหน้าโปรของบอทก่อนนะค่ะ",
            ephemeral=True
        )

    guild_id = interaction.guild.id

    verification_data[guild_id] = {
        "code": None,
        "role_id": role.id
    }

    embed = discord.Embed(
        title="🔐 ระบบยืนยันตัวตน",
        description="กดปุ่มด้านล่างเพื่อรับรหัสใหม่",
        color=0x2f3136
    )

    embed.set_image(url=image_url if image_url else PROMO_IMAGE)

    await channel.send(embed=embed)
    await interaction.response.send_message("🍃สร้างระบบยืนยันตัวตนแล้ว", ephemeral=True)

# ================= READY =================

@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"Logged in as {bot.user}")

bot.run(TOKEN)