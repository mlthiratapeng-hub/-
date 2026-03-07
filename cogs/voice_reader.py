import discord
from discord.ext import commands
from discord import app_commands
from gtts import gTTS
import asyncio
import os

class VoiceReader(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.vc = None
        self.queue = asyncio.Queue()
        bot.loop.create_task(self.player())

    async def player(self):
        await self.bot.wait_until_ready()

        while True:
            text = await self.queue.get()

            tts = gTTS(text=text, lang="th")
            tts.save("tts.mp3")

            if self.vc and not self.vc.is_playing():
                self.vc.play(discord.FFmpegPCMAudio("tts.mp3"))

                while self.vc.is_playing():
                    await asyncio.sleep(1)

            os.remove("tts.mp3")

    @app_commands.command(name="joic", description="ให้บอทเข้าห้องเสียงและอ่านแชท")
    async def joic(self, interaction: discord.Interaction):

        if not interaction.user.voice:
            await interaction.response.send_message(
                "🥡 คุณต้องอยู่ในห้องเสียงก่อน",
                ephemeral=True
            )
            return

        channel = interaction.user.voice.channel

        if self.vc is None:
            self.vc = await channel.connect()
        else:
            await self.vc.move_to(channel)

        await interaction.response.send_message(
            f"🍃 บอทเข้าห้องเสียงแล้ว: {channel.name}"
        )

    @commands.Cog.listener()
    async def on_message(self, message):

        if message.author.bot:
            return

        if self.vc and self.vc.is_connected():

            if message.content.startswith("/"):
                return

            text = message.content

            if len(text) > 200:
                text = text[:200]

            await self.queue.put(text)


async def setup(bot):
    await bot.add_cog(VoiceReader(bot))