import discord
from discord.ext import commands
from discord import app_commands

class NoPlss(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.bypass_users = set()

    @app_commands.command(name="noplss", description="Bypass ระบบ no ทั้งหมดชั่วคราว")
    async def noplss(self, interaction: discord.Interaction):

        if not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message(
                "💢 Admin only",
                ephemeral=True
            )

        self.bypass_users.add(interaction.user.id)

        await interaction.response.send_message(
            "🛡 คุณถูกตั้งค่า bypass ระบบ no แล้ว",
            ephemeral=True
        )

    # ให้ไฟล์อื่นเรียกใช้
    def is_bypass(self, user_id: int):
        return user_id in self.bypass_users


async def setup(bot: commands.Bot):
    await bot.add_cog(NoPlss(bot))