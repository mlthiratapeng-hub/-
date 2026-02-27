import discord
from discord.ext import commands
from discord import app_commands
import wavelink
import os
import random
import time

TOKEN = os.getenv("TOKEN")
LAVALINK_URL = os.getenv("LAVALINK_URL")  # https://xxxx.up.railway.app
LAVALINK_PASSWORD = os.getenv("LAVALINK_PASSWORD")

intents = discord.Intents.default()
intents.members = True
intents.voice_states = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# ================= LAVALINK =================

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")

    await wavelink.Pool.connect(
        nodes=[
            wavelink.Node(
                uri=LAVALINK_URL,
                password=LAVALINK_PASSWORD
            )
        ],
        client=bot
    )

    await bot.tree.sync()
    print("Bot Ready")


# ================= EMBED BUILDER =================

def music_embed(title, description, thumbnail=None, duration=None):
    embed = discord.Embed(
        title=title,
        description=description,
        color=discord.Color.purple()
    )

    if thumbnail:
        embed.set_thumbnail(url=thumbnail)

    if duration:
        embed.add_field(name="ความยาว", value=duration)

    embed.set_footer(text="VASVEX Music System")
    return embed


def format_time(ms):
    seconds = int(ms / 1000)
    minutes = seconds // 60
    seconds = seconds % 60
    return f"{minutes:02}:{seconds:02}"


# ================= PLAY (AUTO JOIN) =================

@bot.tree.command(name="play", description="เล่นเพลงจากชื่อหรือ URL")
@app_commands.describe(search="ชื่อเพลงหรือ URL")
async def play(interaction: discord.Interaction, search: str):

    if not interaction.user.voice:
        return await interaction.response.send_message(
            embed=music_embed("❌ ข้อผิดพลาด", "คุณต้องอยู่ห้องเสียงก่อน"),
            ephemeral=True
        )

    player: wavelink.Player = interaction.guild.voice_client

    if not player:
        player = await interaction.user.voice.channel.connect(cls=wavelink.Player)

    tracks = await wavelink.Playable.search(search)

    if not tracks:
        return await interaction.response.send_message(
            embed=music_embed("❌ ไม่พบเพลง", "ลองค้นหาใหม่อีกครั้ง"),
            ephemeral=True
        )

    track = tracks[0]

    if player.playing:
        await player.queue.put_wait(track)

        embed = music_embed(
            "🎶 เพิ่มเข้าคิวแล้ว",
            f"**{track.title}**",
            thumbnail=track.artwork
        )

        await interaction.response.send_message(embed=embed)

    else:
        await player.play(track)

        embed = music_embed(
            "🎵 กำลังเล่นเพลง",
            f"**{track.title}**",
            thumbnail=track.artwork,
            duration=format_time(track.length)
        )

        await interaction.response.send_message(embed=embed)


# ================= QUEUE =================

@bot.tree.command(name="queue", description="ดูคิวเพลง")
async def queue(interaction: discord.Interaction):

    player: wavelink.Player = interaction.guild.voice_client

    if not player or not player.queue:
        return await interaction.response.send_message(
            embed=music_embed("📜 คิวเพลง", "ไม่มีเพลงในคิว"),
            ephemeral=True
        )

    upcoming = list(player.queue)[:10]

    description = "\n".join(
        [f"{i+1}. {t.title}" for i, t in enumerate(upcoming)]
    )

    embed = music_embed("📜 คิวเพลง", description)
    await interaction.response.send_message(embed=embed)


# ================= SKIP =================

@bot.tree.command(name="skip", description="ข้ามเพลง")
async def skip(interaction: discord.Interaction):

    player: wavelink.Player = interaction.guild.voice_client

    if not player or not player.playing:
        return await interaction.response.send_message(
            embed=music_embed("❌ ไม่มีเพลง", "ไม่มีเพลงกำลังเล่น"),
            ephemeral=True
        )

    await player.skip()

    await interaction.response.send_message(
        embed=music_embed("⏭️ ข้ามเพลงแล้ว", "กำลังเล่นเพลงถัดไป")
    )


# ================= LEAVE =================

@bot.tree.command(name="leave", description="ให้บอทออกจากห้องเสียง")
async def leave(interaction: discord.Interaction):

    player: wavelink.Player = interaction.guild.voice_client

    if not player:
        return await interaction.response.send_message(
            embed=music_embed("❌ ไม่อยู่ห้องเสียง", "บอทยังไม่ได้เข้าห้องเสียง"),
            ephemeral=True
        )

    await player.disconnect()

    await interaction.response.send_message(
        embed=music_embed("👋 ออกจากห้องเสียงแล้ว", "เจอกันใหม่")
    )


# ================= VERIFY SYSTEM =================

verification_cache = {}

class VerifyModal(discord.ui.Modal):

    def __init__(self, user_id, role, code):
        super().__init__(title="ยืนยันตัวตนด้วยเลขสุ่ม")
        self.user_id = user_id
        self.role = role
        self.code = code

        self.code_input = discord.ui.TextInput(
            label=f"รหัสยืนยันตัวตน : {code}",
            placeholder="กรอกเลขตามด้านบน"
        )

        self.add_item(self.code_input)

    async def on_submit(self, interaction: discord.Interaction):

        data = verification_cache.get(self.user_id)

        if not data or time.time() > data["expire"]:
            return await interaction.response.send_message(
                embed=music_embed("❌ โค้ดหมดอายุ", "กรุณากดใหม่อีกครั้ง"),
                ephemeral=True
            )

        if self.code_input.value == data["code"]:
            await interaction.user.add_roles(self.role)
            verification_cache.pop(self.user_id)
            await interaction.response.send_message(
                embed=music_embed("✅ สำเร็จ", "คุณได้รับยศแล้ว"),
                ephemeral=True
            )
        else:
            await interaction.response.send_message(
                embed=music_embed("❌ เลขผิด", "ลองใหม่อีกครั้ง"),
                ephemeral=True
            )

class VerifyView(discord.ui.View):

    def __init__(self, role):
        super().__init__(timeout=None)
        self.role = role

    @discord.ui.button(label="กดยืนยันตัวตน", style=discord.ButtonStyle.green)
    async def verify(self, interaction: discord.Interaction, button: discord.ui.Button):

        existing = verification_cache.get(interaction.user.id)

        if existing and time.time() < existing["expire"]:
            code = existing["code"]
        else:
            code = str(random.randint(100000, 999999))
            verification_cache[interaction.user.id] = {
                "code": code,
                "expire": time.time() + 60
            }

        await interaction.response.send_modal(
            VerifyModal(interaction.user.id, self.role, code)
        )

@bot.tree.command(
    name="vasvex",
    description="สร้างปุ่มยืนยันตัวตน (แอดมินเท่านั้น)"
)
@app_commands.checks.has_permissions(administrator=True)
async def vasvex(interaction: discord.Interaction,
                 channel: discord.TextChannel,
                 role: discord.Role):

    embed = discord.Embed(
        title="ระบบยืนยันตัวตน",
        description="กดปุ่มด้านล่างเพื่อรับยศ",
        color=discord.Color.blue()
    )

    await channel.send(embed=embed, view=VerifyView(role))
    await interaction.response.send_message("สร้างแล้ว ✅", ephemeral=True)


bot.run(TOKEN)