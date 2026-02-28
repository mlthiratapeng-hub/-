import discord
from discord.ext import commands
from discord import app_commands

class VerifyView(discord.ui.View):
    def __init__(self, role: discord.Role):
        super().__init__(timeout=None)
        self.role = role

    @discord.ui.button(label="🍀 Verify", style=discord.ButtonStyle.green, custom_id="verify_button")
    async def verify_button(self, interaction: discord.Interaction, button: discord.ui.Button):

        if self.role in interaction.user.roles:
            return await interaction.response.send_message(
                "🦞 คุณได้รับยศนี้แล้ว",
                ephemeral=True
            )

        try:
            await interaction.user.add_roles(self.role)
            await interaction.response.send_message(
                "🍀 ยืนยันตัวตนสำเร็จ!",
                ephemeral=True
            )
        except:
            await interaction.response.send_message(
                "🙍 บอทไม่สามารถให้ยศได้ (เช็คสิทธิ์)",
                ephemeral=True
            )


class Verify(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # =========================
    # /verify
    # =========================
    @app_commands.command(name="verify", description="สร้างปุ่มยืนยันตัวตน")
    async def verify(self, interaction: discord.Interaction, role: discord.Role):

        if interaction.guild is None:
            return await interaction.response.send_message(
                "💢 ใช้ได้เฉพาะในเซิร์ฟเวอร์",
                ephemeral=True
            )

        if not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message(
                "💢 Admin only",
                ephemeral=True
            )

        embed = discord.Embed(
            title="🔐 ระบบยืนยันตัวตน",
            description="กดปุ่มด้านล่างเพื่อรับยศ",
            color=discord.Color.green()
        )

        view = VerifyView(role)

        await interaction.response.send_message(
            embed=embed,
            view=view
        )


async def setup(bot: commands.Bot):
    await bot.add_cog(Verify(bot))