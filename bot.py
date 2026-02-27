import discord
from discord import app_commands
from discord.ext import commands
import yt_dlp
import asyncio
import os
import random
import time
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("TOKEN")

PROMO_IMAGE = "https://discord.com/channels/1476624073990738022/1476898781290037409/1476919470978240565"

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

song_queues = {}
verification_data = {}

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
            vc.play(source, after=lambda e: asyncio.run_coroutine_threadsafe(play_next(guild), bot.loop))

@bot.tree.command(name="join", description="ให้บอทเข้าห้องเสียง")
async def join(interaction: discord.Interaction):
    await interaction.response.defer()

    if not interaction.user.voice:
        return await interaction.followup.send(embed=promo_embed("🍒 ผิดพลาด", "คุณต้องอยู่ในห้องเสียง"))

    if interaction.guild.voice_client:
        return await interaction.followup.send(embed=promo_embed("🚧 แจ้งเตือน", "บอทอยู่ในห้องแล้ว"))

    await interaction.user.voice.channel.connect()
    await interaction.followup.send(embed=promo_embed("🌿 สำเร็จ", "บอทเข้าห้องเสียงแล้ว"))

@bot.tree.command(name="leave", description="ให้บอทออกจากห้องเสียง")
async def leave(interaction: discord.Interaction):
    await interaction.response.defer()
    vc = interaction.guild.voice_client

    if vc:
        await vc.disconnect()
        await interaction.followup.send(embed=promo_embed("🍅 ออกแล้ว", "บอทออกจากห้องเสียงแล้ว"))
    else:
        await interaction.followup.send(embed=promo_embed("🍒 ผิดพลาด", "บอทไม่ได้อยู่ในห้องเสียง"))

@bot.tree.command(name="play", description="เล่นเพลงจาก YouTube")
@app_commands.describe(query="ชื่อเพลงหรือ URL")
async def play(interaction: discord.Interaction, query: str):
    await interaction.response.defer(thinking=True)

    if not interaction.user.voice:
        return await interaction.followup.send(embed=promo_embed("🍒 ผิดพลาด", "คุณต้องอยู่ในห้องเสียง"))

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

    await interaction.followup.send(embed=promo_embed("🎶 เพิ่มเพลงแล้ว", f"**{title}**"))

@bot.tree.command(name="queue", description="ดูคิวเพลง")
async def queue(interaction: discord.Interaction):
    await interaction.response.defer()

    if interaction.guild.id not in song_queues or not song_queues[interaction.guild.id]:
        return await interaction.followup.send(embed=promo_embed("🕸️ คิวว่าง", "ไม่มีเพลงในคิว"))

    desc = ""
    for i, (_, title) in enumerate(song_queues[interaction.guild.id], 1):
        desc += f"{i}. {title}\n"

    await interaction.followup.send(embed=promo_embed("📜 คิวเพลง", desc))

@bot.tree.command(name="skip", description="ข้ามเพลง")
async def skip(interaction: discord.Interaction):
    await interaction.response.defer()
    vc = interaction.guild.voice_client

    if vc and vc.is_playing():
        vc.stop()
        await interaction.followup.send(embed=promo_embed("⏭ ข้ามแล้ว", "ข้ามเพลงปัจจุบัน"))
    else:
        await interaction.followup.send(embed=promo_embed("🍒 ผิดพลาด", "ไม่มีเพลงกำลังเล่น"))

# ================= AUTO TTS =================

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    vc = message.guild.voice_client if message.guild else None
    if vc and vc.is_connected() and not vc.is_playing():
        try:
            tts_source = discord.FFmpegPCMAudio(
                f"https://translate.google.com/translate_tts?ie=UTF-8&q={message.content}&tl=th&client=tw-ob"
            )
            vc.play(tts_source)
        except:
            pass

    await bot.process_commands(message)

# ================= VERIFICATION SYSTEM =================

class VerifyModal(discord.ui.Modal):
    def __init__(self, guild_id):
        super().__init__(title="ยืนยันตัวตน")
        self.guild_id = guild_id

        self.code_input = discord.ui.TextInput(
            label="กรอกเลขตามที่แสดงด้านบน",
            placeholder="กรอกตัวเลข"
        )
        self.add_item(self.code_input)

    async def on_submit(self, interaction: discord.Interaction):
        data = verification_data.get(self.guild_id)

        if not data:
            return await interaction.response.send_message("🍒 หมดเวลาแล้ว", ephemeral=True)

        if time.time() > data["expire"]:
            del verification_data[self.guild_id]
            return await interaction.response.send_message("🍒 เลขหมดอายุแล้ว", ephemeral=True)

        if self.code_input.value == str(data["code"]):
            role = interaction.guild.get_role(data["role_id"])
            await interaction.user.add_roles(role)
            await interaction.response.send_message("🌿 ยืนยันสำเร็จ", ephemeral=True)
        else:
            await interaction.response.send_message("🍒 เลขไม่ถูกต้อง", ephemeral=True)

class VerifyView(discord.ui.View):
    def __init__(self, guild_id):
        super().__init__(timeout=None)
        self.guild_id = guild_id

    @discord.ui.button(label="ยืนยันตัวตน", style=discord.ButtonStyle.green)
    async def verify(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(VerifyModal(self.guild_id))

@bot.tree.command(name="vasvex", description="สร้างระบบยืนยันตัวตน")
@app_commands.describe(channel="ห้องที่จะส่ง", role="ยศที่จะให้")
async def vasvex(interaction: discord.Interaction, channel: discord.TextChannel, role: discord.Role):
    await interaction.response.defer()

    if not interaction.user.guild_permissions.administrator:
        return await interaction.followup.send("ต้องเป็นแอดมินเท่านั้น")

    code = random.randint(1000, 9999)

    verification_data[interaction.guild.id] = {
        "code": code,
        "role_id": role.id,
        "expire": time.time() + 60
    }

    embed = promo_embed(
        "🚧 ระบบยืนยันตัวตน",
        f"กรอกเลขนี้: **{code}**\nเลขจะหมดอายุใน 1 นาที"
    )

    await channel.send(embed=embed, view=VerifyView(interaction.guild.id))
    await interaction.followup.send("🌿 สร้างระบบยืนยันตัวตนแล้ว")

    await asyncio.sleep(60)
    if interaction.guild.id in verification_data:
        del verification_data[interaction.guild.id]

# ================= READY =================

@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"Logged in as {bot.user}")

bot.run(TOKEN)