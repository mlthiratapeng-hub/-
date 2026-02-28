import discord
from discord.ext import commands
from discord import app_commands
import time
from collections import defaultdict
from database import is_whitelisted

class AntiSpam(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.enabled = {}
        self.message_cache = defaultdict(list)  # เก็บเวลาข้อความแต่ละคน

    # =========================
    # Slash Command: /nospam
    # =========================
    @app_commands.command(name="nospam", description="เปิด/ปิด ระบบกันสแปม")
    async def nospam(self, interaction: discord.Interaction):

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

        current = self.enabled.get(interaction.guild.id, False)
        self.enabled[interaction.guild.id] = not current

        await interaction.response.send_message(
            f"💢 Anti-Spam {'ON' if not current else 'OFF'}",
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

        if is_whitelisted(message.author.id):
            return

        if not self.enabled.get(message.guild.id, False):
            return

        now = time.time()
        user_id = message.author.id

        self.message_cache[user_id].append(now)

        # เก็บเฉพาะข้อความใน 5 วินาทีล่าสุด
        self.message_cache[user_id] = [
            t for t in self.message_cache[user_id] if now - t <= 5
        ]

        # ถ้าเกิน 5 ข้อความใน 5 วิ = สแปม
        if len(self.message_cache[user_id]) >= 5:
            try:
                await message.delete()
                await message.channel.send(
                    f"{message.author.mention} 💢 ห้ามสแปม",
                    delete_after=5
                )
            except:
                pass


# =========================
# โหลด Cog
# =========================
async def setup(bot: commands.Bot):
    await bot.add_cog(AntiSpam(bot))