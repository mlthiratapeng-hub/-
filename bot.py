import discord
from discord import app_commands
from discord.ext import commands
import wavelink
import os
import random

TOKEN = os.getenv("TOKEN")
LAVALINK_URL = os.getenv("LAVALINK_URL")
LAVALINK_PASSWORD = os.getenv("LAVALINK_PASSWORD")

intents = discord.Intents.default()
intents.members = True
intents.voice_states = True

bot = commands.Bot(command_prefix="!", intents=intents)

# ================= LAVALINK =================

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")

    node = wavelink.Node(
        uri=LAVALINK_URL,
        password=LAVALINK_PASSWORD
    )
    await wavelink.Pool.connect(nodes=[node], client=bot)

    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} commands")
    except Exception as e:
        print(e)

# ================= MUSIC SLASH =================

@bot.tree.command(name="join", description="ให้บอทเข้าห้องเสียง")
async def join(interaction: discord.Interaction):
    if not interaction.user.voice:
        return await interaction.response.send_message("คุณต้องอยู่ในห้องเสียงก่อน ❌", ephemeral=True)

    channel = interaction.user.voice.channel
    await channel.connect(cls=wavelink.Player)
    await interaction.response.send_message("เข้าห้องเสียงแล้ว ✅")

@bot.tree.command(name="play", description="เล่นเพลง")
@app_commands.describe(search="ชื่อเพลงหรือ URL")
async def play(interaction: discord.Interaction, search: str):

    if not interaction.user.voice:
        return await interaction.response.send_message("คุณต้องอยู่ในห้องเสียงก่อน ❌", ephemeral=True)

    if not interaction.guild.voice_client:
        await interaction.user.voice.channel.connect(cls=wavelink.Player)

    player: wavelink.Player = interaction.guild.voice_client

    tracks = await wavelink.Playable.search(search)

    if not tracks:
        return await interaction.response.send_message("หาเพลงไม่เจอ ❌", ephemeral=True)

    await player.play(tracks[0])
    await interaction.response.send_message(f"กำลังเล่น: {tracks[0].title} 🎵")

@bot.tree.command(name="leave", description="ให้บอทออกจากห้องเสียง")
async def leave(interaction: discord.Interaction):
    if interaction.guild.voice_client:
        await interaction.guild.voice_client.disconnect()
        await interaction.response.send_message("ออกจากห้องเสียงแล้ว 👋")
    else:
        await interaction.response.send_message("บอทไม่ได้อยู่ในห้องเสียง ❌", ephemeral=True)

# ================= VERIFY SYSTEM =================

class VerifyModal(discord.ui.Modal, title="ยืนยันตัวตน"):
    def __init__(self, correct_code: str, role: discord.Role):
        super().__init__()
        self.correct_code = correct_code
        self.role = role

        self.code_input = discord.ui.TextInput(
            label="กรอกเลขตามที่เห็น",
            required=True
        )
        self.add_item(self.code_input)

    async def on_submit(self, interaction: discord.Interaction):
        if self.code_input.value == self.correct_code:
            await interaction.user.add_roles(self.role)
            await interaction.response.send_message("ยืนยันสำเร็จ ✅ ได้รับยศแล้ว", ephemeral=True)
        else:
            await interaction.response.send_message("เลขไม่ถูกต้อง ❌", ephemeral=True)

class VerifyView(discord.ui.View):
    def __init__(self, code: str, role: discord.Role):
        super().__init__(timeout=None)
        self.code = code
        self.role = role

    @discord.ui.button(label="กดเพื่อยืนยันตัวตน", style=discord.ButtonStyle.green)
    async def verify(self, interaction: discord.Interaction, button: discord.ui.Button):
        modal = VerifyModal(self.code, self.role)
        await interaction.response.send_modal(modal)

@bot.tree.command(name="vasvex", description="สร้างระบบยืนยันตัวตน")
@app_commands.checks.has_permissions(administrator=True)
@app_commands.describe(
    channel="ห้องที่จะส่งปุ่ม",
    role="ยศที่จะให้",
    digits="จำนวนหลักของตัวเลข (เช่น 4 หรือ 6)"
)
async def vasvex(
    interaction: discord.Interaction,
    channel: discord.TextChannel,
    role: discord.Role,
    digits: int
):
    code = "".join([str(random.randint(0,9)) for _ in range(digits)])

    embed = discord.Embed(
        title="ระบบยืนยันตัวตน",
        description=f"กรอกเลขต่อไปนี้:\n\n**{code}**",
        color=discord.Color.blue()
    )

    view = VerifyView(code, role)

    await channel.send(embed=embed, view=view)
    await interaction.response.send_message("สร้างระบบยืนยันเรียบร้อย ✅", ephemeral=True)

@vasvex.error
async def vasvex_error(interaction: discord.Interaction, error):
    if isinstance(error, app_commands.errors.MissingPermissions):
        await interaction.response.send_message("ต้องเป็นแอดมินเท่านั้น ❌", ephemeral=True)

bot.run(TOKEN)