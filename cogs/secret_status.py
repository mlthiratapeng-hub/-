import discord
from discord.ext import commands, tasks
from discord import app_commands
from datetime import datetime
import pytz

ALLOWED_USER_ID = 1155481097753337916
TWITCH_URL = "https://twitch.tv/discord"  # ใส่ twitch อะไรก็ได้

class SecretStatus(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.update_status.start()

    def cog_unload(self):
        self.update_status.cancel()

    @tasks.loop(minutes=1)
    async def update_status(self):

        guild_count = len(self.bot.guilds)
        total_members = sum(g.member_count for g in self.bot.guilds)

        # เวลาไทย
        tz = pytz.timezone("Asia/Bangkok")
        now = datetime.now(tz)

        day = now.strftime("%A")
        time_now = now.strftime("%H:%M")

        stream_title = f"{day} | {time_now} | {guild_count} เซิร์ฟ | {total_members} คน"

        activity = discord.Streaming(
            name=stream_title,
            url=TWITCH_URL
        )

        await self.bot.change_presence(activity=activity)

    @app_commands.command(name="what_do_you_think_it_is")
    async def secret_command(self, interaction: discord.Interaction):

        if interaction.user.id != ALLOWED_USER_ID:
            await interaction.response.send_message(
                "🍅 คุณไม่มีสิทธิ์ใช้คำสั่งนี้",
                ephemeral=True
            )
            return

        await interaction.response.send_message("✅ เปิดโหมดสตรีมแล้ว", ephemeral=True)


async def setup(bot):
    await bot.add_cog(SecretStatus(bot))