import discord
from discord.ext import commands
from discord import app_commands
import time
from collections import defaultdict
from database import is_whitelisted

class AntiNuke(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.enabled = {}
        self.action_log = defaultdict(list)  # เก็บเวลาการลบช่องของแต่ละคน

    # =========================
    # Slash Command: /nonuke
    # =========================
    @app_commands.command(name="nonuke", description="เปิด/ปิด ระบบกันลบห้องรัว (Anti-Nuke)")
    async def nonuke(self, interaction: discord.Interaction):

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
            f"💣 Anti-Nuke {'ON' if not current else 'OFF'}",
            ephemeral=True
        )

    # =========================
    # ตรวจจับการลบช่อง
    # =========================
    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel: discord.abc.GuildChannel):

        guild = channel.guild

        if not self.enabled.get(guild.id, False):
            return

        # ดึง audit log หาคนลบ
        async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.channel_delete):
            user = entry.user
            break
        else:
            return

        if user.bot:
            return

        if is_whitelisted(user.id):
            return

        now = time.time()
        self.action_log[user.id].append(now)

        # เก็บเฉพาะ 10 วิล่าสุด
        self.action_log[user.id] = [
            t for t in self.action_log[user.id] if now - t <= 5
        ]

        # ถ้าลบเกิน 3 ห้องใน 5 วิ
        if len(self.action_log[user.id]) >= 3:
            try:
                member = guild.get_member(user.id)
                if member:
                    await member.ban(reason="Anti-Nuke: ลบห้องรัวเกินกำหนด")
            except:
                pass


# =========================
# โหลด Cog
# =========================
async def setup(bot: commands.Bot):
    await bot.add_cog(AntiNuke(bot))