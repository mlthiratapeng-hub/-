import discord
from discord import app_commands
from discord.ext import commands
import yt_dlp
import asyncio
import os
import random
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("TOKEN")

PROMO_IMAGE = "https://cdn.discordapp.com/attachments/1476624074921738467/1476892902880706691/77a78e76e8b70493bb8615f5b06e36f7.gif"

# 🔥 ใส่ ID ยศที่อนุญาตให้ใช้คำสั่ง
REQUIRED_ROLE_ID = 1476897558679912541  # <<<<<< เปลี่ยนตรงนี้

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

song_queues = {}
verification_data = {}

# ================= ROLE CHECK =================

def has_required_role(interaction: discord.Interaction):
    if not interaction.guild:
        return False

    role_ids = [role.id for role in interaction.user.roles]
    return REQUIRED_ROLE_ID in role_ids


async def role_block(interaction: discord.Interaction):
    if not has_required_role(interaction):
        await interaction.response.send_message(
            "🍅 คุณไม่มียศที่อนุญาตให้ใช้คำสั่งนี้ โปรดเข้าดิสที่หน้าโปรของ
บอทค่ะ",
            ephemeral=True
        )
        return False
    return True

# ================= PROMO EMBED =================

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

@bot.tree.command(name="join", description="ให้บอทเข้าห้องเสียง")
async def join(interaction: discord.Interaction):
    if not await role_block(interaction): return
    await interaction.response.defer()

    if not interaction.user.voice:
        return await interaction.followup.send(embed=promo_embed("❌ ผิดพลาด", "คุณต้องอยู่ในห้องเสียงก่อน"))

    if interaction.guild.voice_client:
        return await interaction.followup.send(embed=promo_embed("⚠ แจ้งเตือน", "บอทอยู่ในห้องแล้ว"))

    await interaction.user.voice.channel.connect()
    await interaction.followup.send(embed=promo_embed("✅ สำเร็จ", "บอทเข้าห้องเสียงแล้ว"))

@bot.tree.command(name="leave", description="ให้บอทออกจากห้องเสียง")
async def leave(interaction: discord.Interaction):
    if not await role_block(interaction): return
    await interaction.response.defer()
    vc = interaction.guild.voice_client

    if vc:
        await vc.disconnect()
        await interaction.followup.send(embed=promo_embed("👋 ออกแล้ว", "บอทออกจากห้องเสียงแล้ว"))
    else:
        await interaction.followup.send(embed=promo_embed("❌ ผิดพลาด", "บอทไม่ได้อยู่ในห้องเสียง"))

@bot.tree.command(name="play", description="เล่นเพลงจาก YouTube")
@app_commands.describe(query="ชื่อเพลงหรือ URL")
async def play(interaction: discord.Interaction, query: str):
    if not await role_block(interaction): return
    await interaction.response.defer(thinking=True)

    if not interaction.user.voice:
        return await interaction.followup.send(embed=promo_embed("❌ ผิดพลาด", "คุณต้องอยู่ในห้องเสียงก่อน"))

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

    await interaction.followup.send(embed=promo_embed("🎵 เพิ่มเพลงแล้ว", f"**{title}**"))

@bot.tree.command(name="queue", description="ดูคิวเพลง")
async def queue(interaction: discord.Interaction):
    if not await role_block(interaction): return
    await interaction.response.defer()

    if interaction.guild.id not in song_queues or not song_queues[interaction.guild.id]:
        return await interaction.followup.send(embed=promo_embed("📭 คิวว่าง", "ไม่มีเพลงในคิว"))

    desc = ""
    for i, (_, title) in enumerate(song_queues[interaction.guild.id], 1):
        desc += f"{i}. {title}\n"

    await interaction.followup.send(embed=promo_embed("📜 คิวเพลง", desc))

@bot.tree.command(name="skip", description="ข้ามเพลง")
async def skip(interaction: discord.Interaction):
    if not await role_block(interaction): return
    await interaction.response.defer()
    vc = interaction.guild.voice_client

    if vc and vc.is_playing():
        vc.stop()
        await interaction.followup.send(embed=promo_embed("⏭ ข้ามแล้ว", "ข้ามเพลงปัจจุบันแล้ว"))
    else:
        await interaction.followup.send(embed=promo_embed("❌ ผิดพลาด", "ไม่มีเพลงกำลังเล่น"))

# ================= VERIFICATION SYSTEM =================

class VerifyModal(discord.ui.Modal):
    def __init__(self, guild_id):
        super().__init__(title="ยืนยันตัวตนด้วยเลขสุ่ม")
        self.guild_id = guild_id

        code = random.randint(100000, 999999)
        verification_data[guild_id]["code"] = code

        self.code_input = discord.ui.TextInput(
            label=f"กรอกรหัส: {code}",
            placeholder="ใส่ตัวเลขด้านบน",
            required=True
        )
        self.add_item(self.code_input)

    async def on_submit(self, interaction: discord.Interaction):
        data = verification_data.get(self.guild_id)

        if not data:
            return await interaction.response.send_message("ระบบยังไม่ถูกสร้าง", ephemeral=True)

        if self.code_input.value == str(data["code"]):
            role = interaction.guild.get_role(data["role_id"])
            if role:
                await interaction.user.add_roles(role)
                await interaction.response.send_message("✅ ยืนยันสำเร็จ", ephemeral=True)
            else:
                await interaction.response.send_message("🥩 ไม่พบยศ", ephemeral=True)
        else:
            await interaction.response.send_message("🍓 เลขไม่ถูกต้อง", ephemeral=True)

class VerifyView(discord.ui.View):
    def __init__(self, guild_id):
        super().__init__(timeout=None)
        self.guild_id = guild_id

    @discord.ui.button(label="🔐 ยืนยันตัวตน", style=discord.ButtonStyle.green)
    async def verify(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(VerifyModal(self.guild_id))

@bot.tree.command(name="vasvex", description="สร้างระบบยืนยันตัวตน")
@app_commands.describe(channel="ห้องที่จะส่ง", role="ยศที่จะให้")
async def vasvex(interaction: discord.Interaction, channel: discord.TextChannel, role: discord.Role):
    if not interaction.user.guild_permissions.administrator:
        return await interaction.response.send_message("ต้องเป็นแอดมินเท่านั้น", ephemeral=True)

    guild_id = interaction.guild.id

    verification_data[guild_id] = {
        "code": None,
        "role_id": role.id
    }

    embed = promo_embed(
        "🔐 ระบบยืนยันตัวตน",
        "กดปุ่มด้านล่างเพื่อรับรหัสใหม่ทุกครั้ง"
    )

    await channel.send(embed=embed, view=VerifyView(guild_id))
    await interaction.response.send_message("สร้างระบบยืนยันตัวตนแล้ว", ephemeral=True)

# ================= READY =================

@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"Logged in as {bot.user}")

bot.run(TOKEN)