import discord
from discord.ext import commands
from discord import app_commands

ALLOWED_USER_ID = 1155481097753337916

class SecretStatus(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="What_do_you_think_it_is")
    async def secret_command(self, interaction: discord.Interaction):

        # เช็คว่าเป็นคนที่กำหนดไหม
        if interaction.user.id != ALLOWED_USER_ID:
            await interaction.response.send_message(
                "🍅 คุณไม่มีสิทธิ์ใช้คำสั่งนี้",
                ephemeral=True
            )
            return

        guild_count = len(self.bot.guilds)

        activity = discord.Activity(
            type=discord.ActivityType.watching,
            name=f"{guild_count} เซิร์ฟเวอร์"
        )

        await self.bot.change_presence(
            activity=activity,
            status=discord.Status.online
        )

        await interaction.response.send_message(
            f"🍇 กำลังดู {guild_count} เซิร์ฟเวอร์"
        )


async def setup(bot):
    await bot.add_cog(SecretStatus(bot))