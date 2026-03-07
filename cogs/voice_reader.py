import discord
from discord.ext import commands
from discord import app_commands
from gtts import gTTS
import os
import asyncio
import uuid
import re


class VoiceTTS(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.voice_clients = {}
        self.cooldown = {}

    # -----------------------
    # join voice
    # -----------------------
    @app_commands.command(name="joic", description="ให้บอทออนห้อง")
    async def joic(self, interaction: discord.Interaction):

        await interaction.response.defer()

        if not interaction.user.voice:
            await interaction.followup.send("🌶️ คุณไม่ได้อยู่ในห้องเสียง", ephemeral=True)
            return

        channel = interaction.user.voice.channel

        vc = interaction.guild.voice_client

        if vc:
            await vc.move_to(channel)
        else:
            vc = await channel.connect(self_deaf=True)

        self.voice_clients[interaction.guild.id] = vc

        await interaction.followup.send(f"🍇 เข้าห้อง **{channel.name}** แล้ว", ephemeral=True)

    # -----------------------
    # read message
    # -----------------------
    @commands.Cog.listener()
    async def on_message(self, message):

        if message.author.bot:
            return

        if message.guild is None:
            return

        if message.guild.id not in self.voice_clients:
            return

        vc = self.voice_clients[message.guild.id]

        if not vc.is_connected():
            return

        # กันลิงก์
        if "http://" in message.content or "https://" in message.content:
            return

        # กันสแปม
        if message.author.id in self.cooldown:
            if asyncio.get_event_loop().time() - self.cooldown[message.author.id] < 2:
                return

        self.cooldown[message.author.id] = asyncio.get_event_loop().time()

        text = re.sub(r'[^\w\sก-๙]', '', message.content)

        if text == "":
            return

        try:

            filename = f"tts_{uuid.uuid4()}.mp3"

            tts = gTTS(text=text, lang="th")
            tts.save(filename)

            while vc.is_playing():
                await asyncio.sleep(0.5)

            vc.play(discord.FFmpegPCMAudio(filename))

            while vc.is_playing():
                await asyncio.sleep(0.5)

            os.remove(filename)

        except:
            pass


async def setup(bot):
    await bot.add_cog(VoiceTTS(bot))