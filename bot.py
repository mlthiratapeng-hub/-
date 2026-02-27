import discord
from discord import app_commands
from discord.ext import commands
import yt_dlp
import asyncio
import os
from urllib.parse import urlparse
from dotenv import load_dotenv
from datetime import timedelta

load_dotenv()
TOKEN = os.getenv("TOKEN")

PROMO_IMAGE = "https://cdn.discordapp.com/attachments/1476624074921738467/1476892902880706691/77a78e76e8b70493bb8615f5b06e36f7.gif"

REQUIRED_GUILD_ID = 1476624073990738022

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

# ================= DATA =================

song_queues = {}
verification_data = {}

protection_settings = {}
user_warnings = {}
spam_tracker = {}
whitelist_users = {}
log_channels = {}
role_action_tracker = {}
channel_delete_tracker = {}

# ================= EMBED =================

def promo_embed(title, desc):
    embed = discord.Embed(title=title, description=desc, color=0x2f3136)
    embed.set_image(url=PROMO_IMAGE)
    return embed

# ================= ADMIN CHECK =================

async def check_admin_permission(interaction):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("💢 ต้องเป็นแอดมินเท่านั้น", ephemeral=True)
        return False

    required_guild = bot.get_guild(REQUIRED_GUILD_ID)
    if not required_guild:
        await interaction.response.send_message("🥩 ไม่พบดิสหลัก", ephemeral=True)
        return False

    if not required_guild.get_member(interaction.user.id):
        await interaction.response.send_message("🍓 ต้องอยู่ดิสหลักก่อน", ephemeral=True)
        return False

    return True

# ================= PROTECTION COMMANDS =================

@bot.tree.command(name="nonuke", description="💣 เปิดระบบกันนุ๊ก")
async def nonuke(interaction: discord.Interaction):
    if not await check_admin_permission(interaction): return
    protection_settings.setdefault(interaction.guild.id, {})["nonuke"] = True
    await interaction.response.send_message("💣 เปิดกันนุ๊กแล้ว", ephemeral=True)

# ================= MESSAGE MONITOR =================

@bot.event
async def on_message(message):
    if message.author.bot or not message.guild:
        return
    await bot.process_commands(message)

# ================= ANTI ROLE NUKE =================

@bot.event
async def on_guild_role_update(before, after):
    guild_id = after.guild.id

    if not protection_settings.get(guild_id, {}).get("nonuke"):
        return

    async for entry in after.guild.audit_logs(limit=1, action=discord.AuditLogAction.role_update):
        user = entry.user

        if guild_id in whitelist_users and user.id in whitelist_users[guild_id]:
            return

        role_action_tracker.setdefault(guild_id, {}).setdefault(user.id, [])
        now = asyncio.get_event_loop().time()
        role_action_tracker[guild_id][user.id].append(now)

        role_action_tracker[guild_id][user.id] = [
            t for t in role_action_tracker[guild_id][user.id] if now - t <= 5
        ]

        if len(role_action_tracker[guild_id][user.id]) >= 4:
            await after.guild.ban(user, reason="Role Nuke detected")

# ================= 🔥 ANTI CHANNEL DELETE =================

@bot.event
async def on_guild_channel_delete(channel):
    guild = channel.guild
    guild_id = guild.id

    if not protection_settings.get(guild_id, {}).get("nonuke"):
        return

    async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.channel_delete):
        user = entry.user

        # ข้าม whitelist
        if guild_id in whitelist_users and user.id in whitelist_users[guild_id]:
            return

        channel_delete_tracker.setdefault(guild_id, {}).setdefault(user.id, [])
        now = asyncio.get_event_loop().time()
        channel_delete_tracker[guild_id][user.id].append(now)

        # เก็บแค่ 5 วิล่าสุด
        channel_delete_tracker[guild_id][user.id] = [
            t for t in channel_delete_tracker[guild_id][user.id] if now - t <= 5
        ]

        # 🔥 ลบ 5 ห้องใน 5 วิ = แบน
        if len(channel_delete_tracker[guild_id][user.id]) >= 5:
            await guild.ban(user, reason="Channel Delete Nuke")

            if guild_id in log_channels:
                log_channel = bot.get_channel(log_channels[guild_id])
                if log_channel:
                    await log_channel.send(f"💣 {user} ถูกแบน (ลบห้องรัว)")

        break

@bot.tree.command(name="nouser", description="👑 ยกเว้นผู้ใช้")
async def nouser(interaction: discord.Interaction, member: discord.Member):
    if not await check_admin_permission(interaction): return
    whitelist_users.setdefault(interaction.guild.id, set()).add(member.id)
    await interaction.response.send_message("🍀 เพิ่มเข้า whitelist แล้ว", ephemeral=True)

@bot.tree.command(name="rewind", description="🔄 เอาผู้ใช้ออกจาก whitelist")
async def rewind(interaction: discord.Interaction, member: discord.Member):
    if not await check_admin_permission(interaction): return
    whitelist_users.setdefault(interaction.guild.id, set()).discard(member.id)
    await interaction.response.send_message("🍗 กลับมาตรวจจับแล้ว", ephemeral=True)

@bot.tree.command(name="logall", description="📜 เปิดระบบบันทึกกิจกรรมทั้งหมด")
async def logall(interaction: discord.Interaction):
    if not interaction.user.guild_permissions.administrator:
        return await interaction.response.send_message("🍄 แอดมินเท่านั้น", ephemeral=True)
    log_channels[interaction.guild.id] = interaction.channel.id
    await interaction.response.send_message("🍏 เปิดระบบ log แล้ว", ephemeral=True)

# ================= MESSAGE MONITOR =================

@bot.event
async def on_message(message):
    if message.author.bot or not message.guild:
        return

    guild_id = message.guild.id

    # LOG SYSTEM
    if guild_id in log_channels:
        log_channel = bot.get_channel(log_channels[guild_id])
        if log_channel:
            await log_channel.send(f"📝 {message.author} : {message.content}")

    # WHITELIST
    if guild_id in whitelist_users and message.author.id in whitelist_users[guild_id]:
        await bot.process_commands(message)
        return

    # ========== NO LINK ==========
    if protection_settings.get(guild_id, {}).get("nolink"):
        if "http://" in message.content or "https://" in message.content:
            user_warnings.setdefault(guild_id, {}).setdefault(message.author.id, 0)
            user_warnings[guild_id][message.author.id] += 1

            warn = user_warnings[guild_id][message.author.id]

            if warn >= 3:
                until = discord.utils.utcnow() + timedelta(days=3)
                await message.author.timeout(until)
                await message.channel.send(f"🦞 {message.author.mention} หมดเวลา 3 วัน")
            else:
                await message.channel.send(f"💢 เตือนครั้งที่ {warn}")
            return

    # ========== NO SPAM ==========
    if protection_settings.get(guild_id, {}).get("nospam"):
        spam_tracker.setdefault(guild_id, {}).setdefault(message.author.id, [])
        now = asyncio.get_event_loop().time()
        spam_tracker[guild_id][message.author.id].append(now)

        spam_tracker[guild_id][message.author.id] = [
            t for t in spam_tracker[guild_id][message.author.id] if now - t <= 5
        ]

        if len(spam_tracker[guild_id][message.author.id]) >= 5:
            user_warnings.setdefault(guild_id, {}).setdefault(message.author.id, 0)
            user_warnings[guild_id][message.author.id] += 1

            if user_warnings[guild_id][message.author.id] >= 3:
                await message.guild.ban(message.author, reason="Spam detected")
                await message.channel.send("🔨 ถูกแบน (Spam)")
            else:
                await message.channel.send("🌼 หยุดสแปม")
            return

    await bot.process_commands(message)

# ================= ANTI NUKE =================

@bot.event
async def on_guild_role_update(before, after):
    guild_id = after.guild.id

    if not protection_settings.get(guild_id, {}).get("nonuke"):
        return

    async for entry in after.guild.audit_logs(limit=1, action=discord.AuditLogAction.role_update):
        user = entry.user

        if guild_id in whitelist_users and user.id in whitelist_users[guild_id]:
            return

        role_action_tracker.setdefault(guild_id, {}).setdefault(user.id, [])
        now = asyncio.get_event_loop().time()
        role_action_tracker[guild_id][user.id].append(now)

        role_action_tracker[guild_id][user.id] = [
            t for t in role_action_tracker[guild_id][user.id] if now - t <= 5
        ]

        if len(role_action_tracker[guild_id][user.id]) >= 4:
            await after.guild.ban(user, reason="Nuke detected")
            if guild_id in log_channels:
                log_channel = bot.get_channel(log_channels[guild_id])
                if log_channel:
                    await log_channel.send(f"💣 {user} ถูกแบน (Nuke)")

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