import discord
from discord.ext import commands
from discord import app_commands
import wavelink
import random
import os

TOKEN = os.getenv("TOKEN")  # ใส่ใน Railway Variables
LAVALINK_URL = os.getenv("LAVALINK_URL")  # เช่น https://xxxx.up.railway.app
LAVALINK_PASSWORD = os.getenv("LAVALINK_PASSWORD")  # ต้องตรงกับ lavalink

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

# ===================== LAVALINK CONNECT =====================

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
        print(f"Synced {len(synced)} slash commands")
    except Exception as e:
        print(e)

# ===================== MUSIC SYSTEM =====================

@bot.command()
async def join(ctx):
    if ctx.author.voice:
        await ctx.author.voice.channel.connect(cls=wavelink.Player)
        await ctx.send("เข้าห้องเสียงแล้ว")

@bot.command()
async def play(ctx, *, search: str):
    if not ctx.voice_client:
        await ctx.invoke(bot.get_command("join"))

    player: wavelink.Player = ctx.voice_client
    tracks = await wavelink.Playable.search(search)

    if not tracks:
        return await ctx.send("หาเพลงไม่เจอ")

    await player.play(tracks[0])
    await ctx.send(f"กำลังเล่น: {tracks[0].title}")

@bot.command()
async def leave(ctx):
    if ctx.voice_client:
        await ctx.voice_client.disconnect()
        await ctx.send("ออกจากห้องเสียงแล้ว")

# ===================== VERIFY SYSTEM =====================

class VerifyModal(discord.ui.Modal, title="ยืนยันตัวตน"):
    code_input = discord.ui.TextInput(label="กรอกเลขตามที่เห็น", required=True)

    def __init__(self, correct_code, role):
        super().__init__()
        self.correct_code = correct_code
        self.role = role

    async def on_submit(self, interaction: discord.Interaction):
        if self.code_input.value == self.correct_code:
            await interaction.user.add_roles(self.role)
            await interaction.response.send_message("ยืนยันสำเร็จ ✅", ephemeral=True)
        else:
            await interaction.response.send_message("เลขไม่ถูกต้อง ❌", ephemeral=True)

class VerifyView(discord.ui.View):
    def __init__(self, code, role):
        super().__init__(timeout=None)
        self.code = code
        self.role = role

    @discord.ui.button(label="ยืนยันตัวตน", style=discord.ButtonStyle.green)
    async def verify_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        modal = VerifyModal(self.code, self.role)
        await interaction.response.send_modal(modal)

# ===================== SLASH COMMAND =====================

@bot.tree.command(name="vasvex", description="สร้างระบบยืนยันตัวตน")
@app_commands.checks.has_permissions(administrator=True)
async def vasvex(
    interaction: discord.Interaction,
    channel: discord.TextChannel,
    role: discord.Role,
    number: str
):
    view = VerifyView(number, role)

    embed = discord.Embed(
        title="ระบบยืนยันตัวตน",
        description=f"กรอกเลขต่อไปนี้:\n\n**{number}**",
        color=discord.Color.blue()
    )

    await channel.send(embed=embed, view=view)
    await interaction.response.send_message("สร้างระบบยืนยันแล้ว ✅", ephemeral=True)

# ===================== ERROR HANDLER =====================

@vasvex.error
async def vasvex_error(interaction: discord.Interaction, error):
    if isinstance(error, app_commands.errors.MissingPermissions):
        await interaction.response.send_message("ต้องเป็นแอดมินเท่านั้น ❌", ephemeral=True)

bot.run(TOKEN)