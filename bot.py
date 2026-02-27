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

# ================= NEW STORAGE =================
welcome_settings = {}
goodbye_settings = {}

# ================= EMBED =================

def promo_embed(title, desc):
    embed = discord.Embed(title=title, description=desc, color=0x2f3136)
    embed.set_image(url=PROMO_IMAGE)
    return embed

# ================= WELCOME / GOODBYE VIEW =================

class StopWelcomeView(discord.ui.View):
    def __init__(self, guild_id):
        super().__init__(timeout=None)
        self.guild_id = guild_id

    @discord.ui.button(label="🔴 หยุด Welcome", style=discord.ButtonStyle.danger)
    async def stop_welcome(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message("💢 แอดมินเท่านั้น", ephemeral=True)

        welcome_settings.pop(self.guild_id, None)
        await interaction.response.send_message("🗯️ ปิดระบบ Welcome แล้ว", ephemeral=True)


class StopGoodbyeView(discord.ui.View):
    def __init__(self, guild_id):
        super().__init__(timeout=None)
        self.guild_id = guild_id

    @discord.ui.button(label="🔴 หยุด Goodbye", style=discord.ButtonStyle.danger)
    async def stop_goodbye(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message("💢 แอดมินเท่านั้น", ephemeral=True)

        goodbye_settings.pop(self.guild_id, None)
        await interaction.response.send_message("💾 ปิดระบบ Goodbye แล้ว", ephemeral=True)

# ================= SET WELCOME =================

@bot.tree.command(name="setwelcome", description="ตั้งค่าข้อความต้อนรับ")
@app_commands.describe(channel="ห้อง", message="ข้อความ (ใช้ {user} {server})")
async def setwelcome(interaction: discord.Interaction,
                     channel: discord.TextChannel,
                     message: str):

    if not interaction.user.guild_permissions.administrator:
        return await interaction.response.send_message("💢 ต้องเป็นแอดมิน", ephemeral=True)

    required_guild = bot.get_guild(REQUIRED_GUILD_ID)
    member = required_guild.get_member(interaction.user.id) if required_guild else None

    if not member:
        return await interaction.response.send_message("💢 ไม่มีสิทธิ์ใช้คำสั่งนี้", ephemeral=True)

    welcome_settings[interaction.guild.id] = {
        "channel_id": channel.id,
        "message": message
    }

    view = StopWelcomeView(interaction.guild.id)

    await interaction.response.send_message(
        "🗯️ เปิดระบบ Welcome แล้ว",
        view=view,
        ephemeral=True
    )

# ================= SET GOODBYE =================

@bot.tree.command(name="setgoodbye", description="ตั้งค่าข้อความลา")
@app_commands.describe(channel="ห้อง", message="ข้อความ (ใช้ {user} {server})")
async def setgoodbye(interaction: discord.Interaction,
                     channel: discord.TextChannel,
                     message: str):

    if not interaction.user.guild_permissions.administrator:
        return await interaction.response.send_message("💢 ต้องเป็นแอดมิน", ephemeral=True)

    required_guild = bot.get_guild(REQUIRED_GUILD_ID)
    member = required_guild.get_member(interaction.user.id) if required_guild else None

    if not member:
        return await interaction.response.send_message("💢 ไม่มีสิทธิ์ใช้คำสั่งนี้", ephemeral=True)

    goodbye_settings[interaction.guild.id] = {
        "channel_id": channel.id,
        "message": message
    }

    view = StopGoodbyeView(interaction.guild.id)

    await interaction.response.send_message(
        "🗯️ เปิดระบบ Goodbye แล้ว",
        view=view,
        ephemeral=True
    )

# ================= MEMBER JOIN =================

@bot.event
async def on_member_join(member):

    guild_id = member.guild.id

    if guild_id not in welcome_settings:
        return

    data = welcome_settings[guild_id]
    channel = bot.get_channel(data["channel_id"])

    if not channel:
        return

    msg = data["message"]
    msg = msg.replace("{user}", member.mention)
    msg = msg.replace("{server}", member.guild.name)

    embed = discord.Embed(
        title="📁 สมาชิกใหม่เข้าแล้ว",
        description=msg,
        color=0x2f3136
    )

    embed.set_thumbnail(url=member.display_avatar.url)

    await channel.send(embed=embed)

# ================= MEMBER LEAVE =================

@bot.event
async def on_member_remove(member):

    guild_id = member.guild.id

    if guild_id not in goodbye_settings:
        return

    data = goodbye_settings[guild_id]
    channel = bot.get_channel(data["channel_id"])

    if not channel:
        return

    msg = data["message"]
    msg = msg.replace("{user}", member.name)
    msg = msg.replace("{server}", member.guild.name)

    embed = discord.Embed(
        title="💢 สมาชิกออกจากเซิร์ฟเวอร์",
        description=msg,
        color=0x2f3136
    )

    embed.set_thumbnail(url=member.display_avatar.url)

    await channel.send(embed=embed)

# ================= EMBED =================

def promo_embed(title, desc):
    embed = discord.Embed(title=title, description=desc, color=0x2f3136)
    embed.set_image(url=PROMO_IMAGE)
    return embed

def check_link_safety(url):
    parsed = urlparse(url)
    score = 100

    if not parsed.scheme or not parsed.netloc:
        return 0, "ลิงก์ไม่ถูกต้อง"

    # ไม่ใช่ https ลดคะแนน
    if parsed.scheme != "https":
        score -= 30

    # คำต้องสงสัย
    suspicious_words = [
        "login", "verify", "account", "update",
        "free", "gift", "nitro", "steam",
        "bonus", "claim", "secure"
    ]

    for word in suspicious_words:
        if word in url.lower():
            score -= 10

    # โดเมนยาวผิดปกติ
    if len(parsed.netloc) > 30:
        score -= 10

    # มี @ ในลิงก์ (เทคนิค phishing)
    if "@" in url:
        score -= 20

    if score < 0:
        score = 0

    if score >= 80:
        status = "🍀 ปลอดภัยสูง"
    elif score >= 50:
        status = "🍊 เสี่ยงปานกลาง"
    else:
        status = "🍎 เสี่ยงสูง"

    return score, status


@bot.command(name="link")
async def link_check(ctx, url: str):
    score, status = check_link_safety(url)

    embed = discord.Embed(
        title="🔍 ผลการตรวจสอบลิงก์",
        color=0x2f3136
    )

    embed.add_field(name="🔗 ลิงก์", value=url, inline=False)
    embed.add_field(name="📊 ความปลอดภัย", value=f"{score}%", inline=True)
    embed.add_field(name="📌 สถานะ", value=status, inline=True)
    embed.set_image(url=PROMO_IMAGE)

    await ctx.send(embed=embed)

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