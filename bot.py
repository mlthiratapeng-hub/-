import discord
from discord.ext import commands
from discord import app_commands
import wavelink
import os
import random
import time
import gtts
from io import BytesIO

TOKEN = os.getenv("TOKEN")
LAVALINK_URL = os.getenv("LAVALINK_URL")
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

    node = wavelink.Node(
        uri=LAVALINK_URL,
        password=LAVALINK_PASSWORD
    )

    await wavelink.Pool.connect(nodes=[node], client=bot)
    await bot.tree.sync()
    print("Bot Ready")


class Player(wavelink.Player):
    def __init__(self):
        super().__init__()
        self.queue = []

    async def play_next(self):
        if self.queue:
            await self.play(self.queue.pop(0))


@bot.event
async def on_wavelink_track_end(player: Player, track, reason):
    await player.play_next()

# ================= JOIN =================

@bot.tree.command(name="join", description="ให้บอทเข้าห้องเสียงของคุณ")
async def join(interaction: discord.Interaction):

    if not interaction.user.voice:
        return await interaction.response.send_message(
            "คุณต้องอยู่ห้องเสียงก่อน ❌", ephemeral=True
        )

    channel = interaction.user.voice.channel

    if interaction.guild.voice_client:
        await interaction.guild.voice_client.move_to(channel)
    else:
        await channel.connect(cls=Player)

    await interaction.response.send_message("เข้าห้องเสียงแล้ว ✅")

# ================= PLAY =================

@bot.tree.command(name="play", description="เล่นเพลงจากชื่อหรือ URL")
@app_commands.describe(search="ชื่อเพลงหรือ URL")
async def play(interaction: discord.Interaction, search: str):

    if not interaction.user.voice:
        return await interaction.response.send_message(
            "คุณต้องอยู่ห้องเสียงก่อน ❌", ephemeral=True
        )

    if not interaction.guild.voice_client:
        await interaction.user.voice.channel.connect(cls=Player)

    player: Player = interaction.guild.voice_client

    tracks = await wavelink.Playable.search(search)
    if not tracks:
        return await interaction.response.send_message(
            "หาเพลงไม่เจอ ❌", ephemeral=True
        )

    track = tracks[0]

    if player.playing:
        player.queue.append(track)
        await interaction.response.send_message(f"เพิ่มเข้าคิว: {track.title}")
    else:
        await player.play(track)
        await interaction.response.send_message(f"กำลังเล่น: {track.title}")

# ================= QUEUE =================

@bot.tree.command(name="queue", description="ดูเพลงที่กำลังเล่นและคิวเพลง")
async def queue(interaction: discord.Interaction):

    player: Player = interaction.guild.voice_client

    if not player:
        return await interaction.response.send_message(
            "บอทยังไม่อยู่ในห้องเสียง ❌", ephemeral=True
        )

    now_playing = player.current.title if player.current else "ไม่มีเพลงกำลังเล่น"

    if not player.queue:
        return await interaction.response.send_message(
            f"กำลังเล่น: {now_playing}\n\nไม่มีเพลงในคิว"
        )

    queue_list = "\n".join(
        [f"{i+1}. {t.title}" for i, t in enumerate(player.queue[:10])]
    )

    await interaction.response.send_message(
        f"กำลังเล่น: {now_playing}\n\nคิวเพลง:\n{queue_list}"
    )

# ================= SKIP =================

@bot.tree.command(name="skip", description="ข้ามเพลงปัจจุบัน")
async def skip(interaction: discord.Interaction):

    player: Player = interaction.guild.voice_client

    if not player or not player.playing:
        return await interaction.response.send_message(
            "ไม่มีเพลงให้ข้าม ❌", ephemeral=True
        )

    await player.stop()
    await interaction.response.send_message("ข้ามเพลงแล้ว ⏭️")

# ================= STOP =================

@bot.tree.command(name="stop", description="หยุดเพลงและล้างคิวทั้งหมด")
async def stop(interaction: discord.Interaction):

    player: Player = interaction.guild.voice_client

    if not player:
        return await interaction.response.send_message(
            "บอทยังไม่อยู่ในห้องเสียง ❌", ephemeral=True
        )

    player.queue.clear()
    await player.stop()
    await interaction.response.send_message("หยุดเพลงและล้างคิวแล้ว ⛔")

# ================= LEAVE =================

@bot.tree.command(name="leave", description="ให้บอทออกจากห้องเสียง")
async def leave(interaction: discord.Interaction):

    if interaction.guild.voice_client:
        await interaction.guild.voice_client.disconnect()
        await interaction.response.send_message("ออกจากห้องเสียงแล้ว 👋")
    else:
        await interaction.response.send_message(
            "บอทยังไม่อยู่ในห้องเสียง ❌", ephemeral=True
        )

# ================= TTS SYSTEM =================

@bot.event
async def on_message(message):

    if message.author.bot:
        return

    if not message.guild:
        return

    voice = message.guild.voice_client
    if not voice:
        return

    # ถ้ามีเพลงกำลังเล่น → ไม่อ่าน
    if isinstance(voice, Player) and voice.playing:
        return

    # อ่านเฉพาะคนที่อยู่ห้องเดียวกับบอท
    if message.author.voice and message.author.voice.channel == voice.channel:

        tts = gtts.gTTS(message.content, lang="th")
        fp = BytesIO()
        tts.write_to_fp(fp)
        fp.seek(0)

        source = discord.FFmpegPCMAudio(fp, pipe=True)
        voice.play(source)

    await bot.process_commands(message)

# ================= VERIFY =================

verification_cache = {}

class VerifyModal(discord.ui.Modal, title="ยืนยันตัวตน"):
    def __init__(self, user_id, role):
        super().__init__()
        self.user_id = user_id
        self.role = role

        self.code_input = discord.ui.TextInput(label="กรอกเลข")
        self.add_item(self.code_input)

    async def on_submit(self, interaction: discord.Interaction):

        data = verification_cache.get(self.user_id)

        if not data or time.time() > data["expire"]:
            return await interaction.response.send_message(
                "โค้ดหมดอายุ ❌", ephemeral=True
            )

        if self.code_input.value == data["code"]:
            await interaction.user.add_roles(self.role)
            verification_cache.pop(self.user_id)
            await interaction.response.send_message(
                "ยืนยันสำเร็จ ✅", ephemeral=True
            )
        else:
            await interaction.response.send_message(
                "เลขผิด ❌", ephemeral=True
            )

class VerifyView(discord.ui.View):
    def __init__(self, role):
        super().__init__(timeout=None)
        self.role = role

    @discord.ui.button(label="กดยืนยันตัวตน", style=discord.ButtonStyle.green)
    async def verify(self, interaction: discord.Interaction, button: discord.ui.Button):

        code = str(random.randint(100000, 999999))

        verification_cache[interaction.user.id] = {
            "code": code,
            "expire": time.time() + 60
        }

        await interaction.response.send_modal(
            VerifyModal(interaction.user.id, self.role)
        )

        await interaction.followup.send(
            f"กรอกเลขนี้ภายใน 1 นาที:\n**{code}**",
            ephemeral=True
        )

@bot.tree.command(
    name="vasvex",
    description="สร้างปุ่มยืนยันตัวตน (เฉพาะแอดมินเท่านั้น)"
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