import discord
from discord.ext import commands
from discord import app_commands
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

    await bot.tree.sync()
    print("Slash commands synced")

# ================= MUSIC SYSTEM =================

class Player(wavelink.Player):
    def __init__(self):
        super().__init__()
        self.queue = []
        self.playing_now = None

    async def play_next(self):
        if self.queue:
            track = self.queue.pop(0)
            self.playing_now = track
            await self.play(track)

@bot.tree.command(name="join")
async def join(interaction: discord.Interaction):
    if not interaction.user.voice:
        return await interaction.response.send_message("คุณต้องอยู่ห้องเสียงก่อน ❌", ephemeral=True)

    await interaction.user.voice.channel.connect(cls=Player)
    await interaction.response.send_message("เข้าห้องเสียงแล้ว ✅")

@bot.tree.command(name="play")
@app_commands.describe(search="ชื่อเพลงหรือ URL")
async def play(interaction: discord.Interaction, search: str):

    if not interaction.user.voice:
        return await interaction.response.send_message("คุณต้องอยู่ห้องเสียงก่อน ❌", ephemeral=True)

    if not interaction.guild.voice_client:
        await interaction.user.voice.channel.connect(cls=Player)

    player: Player = interaction.guild.voice_client

    tracks = await wavelink.Playable.search(search)
    if not tracks:
        return await interaction.response.send_message("หาเพลงไม่เจอ ❌", ephemeral=True)

    track = tracks[0]

    if player.playing:
        player.queue.append(track)
        await interaction.response.send_message(f"เพิ่มเข้าคิว: {track.title} 📜")
    else:
        await player.play(track)
        await interaction.response.send_message(f"กำลังเล่น: {track.title} 🎵")

@bot.tree.command(name="skip")
async def skip(interaction: discord.Interaction):
    player: Player = interaction.guild.voice_client
    if player and player.playing:
        await player.stop()
        await interaction.response.send_message("ข้ามเพลง ⏭️")
    else:
        await interaction.response.send_message("ไม่มีเพลงกำลังเล่น ❌", ephemeral=True)

@bot.tree.command(name="stop")
async def stop(interaction: discord.Interaction):
    player: Player = interaction.guild.voice_client
    if player:
        player.queue.clear()
        await player.stop()
        await interaction.response.send_message("หยุดเพลงและล้างคิว ⛔")
    else:
        await interaction.response.send_message("บอทไม่ได้อยู่ในห้องเสียง ❌", ephemeral=True)

@bot.tree.command(name="pause")
async def pause(interaction: discord.Interaction):
    player: Player = interaction.guild.voice_client
    if player and player.playing:
        await player.pause(True)
        await interaction.response.send_message("พักเพลง ⏸️")
    else:
        await interaction.response.send_message("ไม่มีเพลงกำลังเล่น ❌", ephemeral=True)

@bot.tree.command(name="resume")
async def resume(interaction: discord.Interaction):
    player: Player = interaction.guild.voice_client
    if player:
        await player.pause(False)
        await interaction.response.send_message("เล่นต่อ ▶️")
    else:
        await interaction.response.send_message("บอทไม่ได้อยู่ในห้องเสียง ❌", ephemeral=True)

@bot.tree.command(name="volume")
@app_commands.describe(level="ระดับเสียง 0-100")
async def volume(interaction: discord.Interaction, level: int):
    player: Player = interaction.guild.voice_client
    if player:
        await player.set_volume(level)
        await interaction.response.send_message(f"ตั้งเสียงเป็น {level}% 🔊")
    else:
        await interaction.response.send_message("บอทไม่ได้อยู่ในห้องเสียง ❌", ephemeral=True)

@bot.tree.command(name="leave")
async def leave(interaction: discord.Interaction):
    if interaction.guild.voice_client:
        await interaction.guild.voice_client.disconnect()
        await interaction.response.send_message("ออกจากห้องเสียง 👋")
    else:
        await interaction.response.send_message("บอทไม่ได้อยู่ในห้องเสียง ❌", ephemeral=True)

@bot.event
async def on_wavelink_track_end(player: Player, track, reason):
    await player.play_next()

# ================= VERIFY SYSTEM =================

class VerifyModal(discord.ui.Modal, title="ยืนยันตัวตน"):
    def __init__(self, correct_code: str, role: discord.Role):
        super().__init__()
        self.correct_code = correct_code
        self.role = role

        self.code_input = discord.ui.TextInput(label="กรอกเลขตามที่เห็น", required=True)
        self.add_item(self.code_input)

    async def on_submit(self, interaction: discord.Interaction):
        if self.code_input.value == self.correct_code:
            await interaction.user.add_roles(self.role)
            await interaction.response.send_message("ยืนยันสำเร็จ ✅", ephemeral=True)
        else:
            await interaction.response.send_message("เลขไม่ถูกต้อง ❌", ephemeral=True)

class VerifyView(discord.ui.View):
    def __init__(self, code: str, role: discord.Role):
        super().__init__(timeout=None)
        self.code = code
        self.role = role

    @discord.ui.button(label="กดเพื่อยืนยันตัวตน", style=discord.ButtonStyle.green)
    async def verify(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(VerifyModal(self.code, self.role))

@bot.tree.command(name="vasvex")
@app_commands.checks.has_permissions(administrator=True)
@app_commands.describe(
    channel="ห้องที่จะส่งปุ่ม",
    role="ยศที่จะให้",
    digits="จำนวนหลักของเลข เช่น 4 หรือ 6"
)
async def vasvex(interaction: discord.Interaction,
                 channel: discord.TextChannel,
                 role: discord.Role,
                 digits: int):

    code = "".join(str(random.randint(0, 9)) for _ in range(digits))

    embed = discord.Embed(
        title="ระบบยืนยันตัวตน",
        description=f"กรอกเลขนี้:\n\n**{code}**",
        color=discord.Color.blue()
    )

    view = VerifyView(code, role)

    await channel.send(embed=embed, view=view)
    await interaction.response.send_message("สร้างระบบยืนยันแล้ว ✅", ephemeral=True)

@vasvex.error
async def vasvex_error(interaction: discord.Interaction, error):
    if isinstance(error, app_commands.errors.MissingPermissions):
        await interaction.response.send_message("ต้องเป็นแอดมินเท่านั้น ❌", ephemeral=True)

bot.run(TOKEN)