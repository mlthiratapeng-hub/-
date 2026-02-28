import discord
from discord import app_commands
from discord.ext import commands
import random

class VerifyModal(discord.ui.Modal):
    def __init__(self, role: discord.Role, code: str):
        super().__init__(title="ยืนยันตัวตนด้วยเลขสุ่ม")
        self.role = role
        self.code = code

        self.code_input = discord.ui.TextInput(
            label=f"รหัสยืนยันตัวตน: {code}",
            placeholder="กรอกตัวเลขให้ถูกต้อง",
            required=True,
            max_length=6
        )

        self.add_item(self.code_input)

    async def on_submit(self, interaction: discord.Interaction):
        if self.code_input.value == self.code:
            await interaction.user.add_roles(self.role)
            await interaction.response.send_message(
                f"🍀 ยืนยันตัวตนสำเร็จ ได้รับยศ {self.role.mention}",
                ephemeral=True
            )
        else:
            await interaction.response.send_message(
                "💢 รหัสไม่ถูกต้อง ลองกดปุ่มใหม่อีกครั้ง",
                ephemeral=True
            )


class VerifyView(discord.ui.View):
    def __init__(self, role: discord.Role):
        super().__init__(timeout=None)
        self.role = role

    @discord.ui.button(label="Verify", style=discord.ButtonStyle.green, emoji="🍗")
    async def verify_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        random_code = str(random.randint(100000, 999999))
        modal = VerifyModal(self.role, random_code)
        await interaction.response.send_modal(modal)


class Verify(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="verify_identity", description="สร้างระบบยืนยันตัวตน")
    @app_commands.describe(
        role="เลือกยศที่จะให้หลังยืนยัน",
        channel="เลือกช่องที่จะส่งระบบ"
    )
    async def verify_identity(
        self,
        interaction: discord.Interaction,
        role: discord.Role,
        channel: discord.TextChannel
    ):
        embed = discord.Embed(
            title="🔐 System | Verify",
            description=(
                "• กดปุ่มด้านล่างเพื่อยืนยันตัวตน\n"
                "• ระบบจะสุ่มเลขใหม่ทุกครั้งที่กด\n"
                "• ใส่เลขให้ถูกต้องเพื่อรับยศ"
            ),
            color=discord.Color.green()
        )

        await channel.send(embed=embed, view=VerifyView(role))

        await interaction.response.send_message(
            f"🍲 ส่งระบบยืนยันตัวตนไปที่ {channel.mention} แล้ว",
            ephemeral=True
        )


async def setup(bot):
    await bot.add_cog(Verify(bot))