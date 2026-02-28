import discord
from discord.ext import commands
from discord import app_commands
import re
from database import is_whitelisted

class AntiLink(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.enabled = {}  # เก็บสถานะเปิด/ปิด แยกตามเซิร์ฟเวอร์

    # =========================
    # Slash Command: /nolink
    # =========================
    @app_commands.command(name="nolink", description="เปิด/ปิด ระบบกันลิงก์")
    async def nolink(self, interaction: discord.Interaction):

        if interaction.guild is None:
            return await interaction.response.send_message(
                "💢 ใช้ได้เฉพาะในเซิร์ฟเวอร์",
                ephemeral=True
            )

        # ใช้ได้เฉพาะแอดมิน
        if not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message(
                "💢 Admin only",
                ephemeral=True
            )

        current = self.enabled.get(interaction.guild.id, False)
        self.enabled[interaction.guild.id] = not current

        await interaction.response.send_message(
            f"🔗 Anti-Link {'ON' if not current else 'OFF'}",
            ephemeral=True
        )

    # =========================
    # ตรวจข้อความ
    # =========================
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):

        if message.author.bot:
            return

        if not message.guild:
            return

        # ข้ามคนที่ whitelist
        if is_whitelisted(message.author.id):
            return

        # ถ้ายังไม่เปิดระบบ
        if not self.enabled.get(message.guild.id, False):
            return

        # ตรวจจับลิงก์
        if re.search(r"https?://", message.content):
            try:
                await message.delete()
                await message.channel.send(
                    f"{message.author.mention} 💢 ห้ามส่งลิงก์",
                    delete_after=5
                )
            except:
                pass


# =========================
# โหลด Cog
# =========================
async def setup(bot: commands.Bot):
    await bot.add_cog(AntiLink(bot))