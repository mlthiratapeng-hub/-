
import discord
from discord.ext import commands, tasks
from discord import app_commands

ALLOWED_USER_ID = 1155481097753337916


class SecretStatus(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="what_do_you_think_it_is")
    async def secret_command(self, interaction: discord.Interaction):

        if interaction.user.id != ALLOWED_USER_ID:
            await interaction.response.send_message(
                "🍅 คุณไม่มีสิทธิ์ใช้คำสั่งนี้",
                ephemeral=True
            )
            return

        self.update_status.start()

        await interaction.response.send_message(
            "✅ เปิดระบบสถานะแล้ว",
            ephemeral=True
        )

    @tasks.loop(seconds=10)
    async def update_status(self):

        await self.bot.wait_until_ready()

        guild_count = len(self.bot.guilds)

        total_members = 0

        for guild in self.bot.guilds:
            total_members += guild.member_count  # รวมคน+บอท

        status_text = f"🍃 | {guild_count}เซิร์ฟ | {total_members}คน"

        await self.bot.change_presence(
            status=discord.Status.online,  # จุดเขียว
            activity=discord.CustomActivity(name=status_text)
        )


async def setup(bot):
    await bot.add_cog(SecretStatus(bot))