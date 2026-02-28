import discord
from discord.ext import commands
from discord import app_commands
import re
from database import is_whitelisted

class AntiLink(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.enabled = {}      # เปิด/ปิดระบบแยกตามเซิร์ฟเวอร์
        self.warnings = {}     # เก็บจำนวนครั้งที่ส่งลิงก์

    # =========================
    # /nolink เปิด/ปิดระบบ
    # =========================
    @app_commands.command(name="nolink", description="เปิด/ปิด ระบบกันลิงก์")
    async def nolink(self, interaction: discord.Interaction):

        if interaction.guild is None:
            return await interaction.response.send_message(
                "❌ ใช้ได้เฉพาะในเซิร์ฟเวอร์",
                ephemeral=True
            )

        if not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message(
                "❌ Admin only",
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

        # ข้าม whitelist
        if is_whitelisted(message.author.id):
            return

        # ถ้ายังไม่เปิดระบบ
        if not self.enabled.get(message.guild.id, False):
            return

        # ตรวจลิงก์
        if re.search(r"https?://", message.content):

            try:
                await message.delete()
            except:
                pass

            key = (message.guild.id, message.author.id)
            self.warnings[key] = self.warnings.get(key, 0) + 1

            count = self.warnings[key]

            # เตือนครั้งที่ 1-2
            if count < 3:
                await message.channel.send(
                    f"⚠ {message.author.mention} ห้ามส่งลิงก์ ({count}/3)",
                    delete_after=5
                )
                return

            # ครบ 3 ครั้ง → แบน
            try:
                await message.author.ban(reason="ส่งลิงก์ครบ 3 ครั้ง")
                await message.channel.send(
                    f"🔨 {message.author.mention} ถูกแบน (ส่งลิงก์ครบ 3 ครั้ง)",
                    delete_after=5
                )
            except Exception as e:
                print("BAN ERROR:", e)

            # รีเซ็ตตัวนับ
            self.warnings.pop(key, None)


async def setup(bot: commands.Bot):
    await bot.add_cog(AntiLink(bot))