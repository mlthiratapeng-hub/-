import discord
from discord.ext import commands, tasks
from discord import app_commands
import wavelink
import asyncio
from datetime import timedelta

# ==============================
# 🎵 Utility
# ==============================

def format_time(ms: int):
    seconds = int(ms / 1000)
    return str(timedelta(seconds=seconds))

def progress_bar(position, length):
    total = 20
    filled = int((position / length) * total) if length > 0 else 0
    return "▰" * filled + "▱" * (total - filled)

# ==============================
# 🎛 UI VIEW
# ==============================

class MusicView(discord.ui.View):
    def __init__(self, player):
        super().__init__(timeout=None)
        self.player = player

    @discord.ui.button(label="⏮", style=discord.ButtonStyle.secondary)
    async def back(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("🍅 ยังไม่รองรับย้อนเพลง", ephemeral=True)

    @discord.ui.button(label="⏯", style=discord.ButtonStyle.primary)
    async def pause_resume(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.player.paused:
            await self.player.pause(False)
            await interaction.response.send_message("▶ เล่นต่อ", ephemeral=True)
        else:
            await self.player.pause(True)
            await interaction.response.send_message("⏸ หยุดชั่วคราว", ephemeral=True)

    @discord.ui.button(label="⏭", style=discord.ButtonStyle.secondary)
    async def skip(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.player.skip()
        await interaction.response.send_message("⏭ ข้ามเพลง", ephemeral=True)

    @discord.ui.button(label="⏹", style=discord.ButtonStyle.danger)
    async def stop(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.player.disconnect()
        await interaction.response.send_message("⏹ หยุดทั้งหมด", ephemeral=True)

    @discord.ui.button(label="📄", style=discord.ButtonStyle.secondary)
    async def queue(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self.player.queue:
            await interaction.response.send_message("ไม่มีเพลงในคิว", ephemeral=True)
            return

        desc = ""
        for i, track in enumerate(self.player.queue, start=1):
            desc += f"{i}. {track.title}\n"

        embed = discord.Embed(
            title="📜 คิวเพลง",
            description=desc[:4000],
            color=discord.Color.blue()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(label="🔉", style=discord.ButtonStyle.secondary)
    async def vol_down(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.player.set_volume(max(self.player.volume - 10, 0))
        await interaction.response.send_message("🔉 ลดเสียง", ephemeral=True)

    @discord.ui.button(label="🔊", style=discord.ButtonStyle.secondary)
    async def vol_up(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.player.set_volume(min(self.player.volume + 10, 200))
        await interaction.response.send_message("🔊 เพิ่มเสียง", ephemeral=True)

# ==============================
# 🎵 COG
# ==============================

class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.now_playing_message = {}

    @app_commands.command(name="play", description="เล่นเพลง")
    async def play(self, interaction: discord.Interaction, query: str):

        if not interaction.user.voice:
            await interaction.response.send_message("เข้าห้องเสียงก่อน", ephemeral=True)
            return

        await interaction.response.defer()

        channel = interaction.user.voice.channel

        if not interaction.guild.voice_client:
            player = await channel.connect(cls=wavelink.Player)
        else:
            player = interaction.guild.voice_client

        tracks = await wavelink.Playable.search(query)
        if not tracks:
            await interaction.followup.send("ไม่พบเพลง")
            return

        track = tracks[0]

        if player.playing:
            await player.queue.put_wait(track)
            await interaction.followup.send(f"🥕 เพิ่มเข้าคิว: {track.title}")
            return

        await player.play(track)
        await player.set_volume(80)

        embed = discord.Embed(
            title="🎵 Now Playing",
            description=f"**{track.title}**\n{track.author}",
            color=discord.Color.purple()
        )

        embed.set_thumbnail(url=track.artwork)
        embed.add_field(
            name="⏱ เวลา",
            value=f"`00:00` {progress_bar(0, track.length)} `{format_time(track.length)}`",
            inline=False
        )

        view = MusicView(player)

        msg = await interaction.followup.send(embed=embed, view=view)
        self.now_playing_message[player.guild.id] = msg

        self.update_progress.start(player, track)

    @tasks.loop(seconds=5)
    async def update_progress(self, player, track):

        if not player.playing:
            self.update_progress.stop()
            return

        msg = self.now_playing_message.get(player.guild.id)
        if not msg:
            return

        position = player.position

        embed = discord.Embed(
            title="🎵 Now Playing",
            description=f"**{track.title}**\n{track.author}",
            color=discord.Color.purple()
        )

        embed.set_thumbnail(url=track.artwork)
        embed.add_field(
            name="⏱ เวลา",
            value=f"`{format_time(position)}` {progress_bar(position, track.length)} `{format_time(track.length)}`",
            inline=False
        )

        await msg.edit(embed=embed, view=MusicView(player))

    @commands.Cog.listener()
    async def on_wavelink_track_end(self, payload):
        player = payload.player

        if player.queue:
            next_track = await player.queue.get_wait()
            await player.play(next_track)
            self.update_progress.start(player, next_track)

async def setup(bot):
    await bot.add_cog(Music(bot))