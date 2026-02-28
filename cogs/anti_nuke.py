import discord
from discord.ext import commands
from discord import app_commands
import time
from collections import defaultdict
from database import is_whitelisted

anti_nuke_status = {}

class AntiNukeToggleView(discord.ui.View):
    def __init__(self, guild_id):
        super().__init__(timeout=60)
        self.guild_id = guild_id

    @discord.ui.button(label="เปิดระบบ", style=discord.ButtonStyle.success, emoji="📁")
    async def enable(self, interaction: discord.Interaction, button: discord.ui.Button):
        anti_nuke_status[self.guild_id] = True

        embed = discord.Embed(
            title="💣 ระบบป้องกันการลบห้องรัวลบยศสร้างห้อง (Anti-Nuke)",
            description="📁 เปิดระบบเรียบร้อยแล้ว",
            color=discord.Color.green()
        )
        await interaction.response.edit_message(embed=embed, view=None)

    @discord.ui.button(label="ปิดระบบ", style=discord.ButtonStyle.danger, emoji="💢")
    async def disable(self, interaction: discord.Interaction, button: discord.ui.Button):
        anti_nuke_status[self.guild_id] = False

        embed = discord.Embed(
            title="💣 ระบบป้องกันการลบห้องรัว (Anti-Nuke)",
            description="💢 ปิดระบบเรียบร้อยแล้ว",
            color=discord.Color.red()
        )
        await interaction.response.edit_message(embed=embed, view=None)


class AntiNukeMainView(discord.ui.View):
    def __init__(self, guild_id):
        super().__init__(timeout=60)
        self.guild_id = guild_id

    @discord.ui.button(label="เลือกการตั้งค่า", style=discord.ButtonStyle.primary)
    async def settings(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="💣 ตั้งค่าระบบป้องกันการลบห้องรัว",
            description="เลือกระบบที่ต้องการด้านล่างค่ะ...",
            color=discord.Color.blurple()
        )

        await interaction.response.edit_message(
            embed=embed,
            view=AntiNukeToggleView(self.guild_id)
        )


class AntiNuke(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.action_log = defaultdict(list)

    @app_commands.command(name="anti-nuke", description="ตั้งค่าระบบป้องกันการลบห้องรัว")
    async def anti_nuke(self, interaction: discord.Interaction):

        guild_id = interaction.guild.id

        if guild_id not in anti_nuke_status:
            anti_nuke_status[guild_id] = False

        embed = discord.Embed(
            title="💣 ตั้งค่าระบบป้องกันการลบห้องรัว",
            description="กดปุ่มด้านล่างเพื่อจัดการระบบ",
            color=discord.Color.blurple()
        )

        embed.add_field(
            name="สถานะปัจจุบัน",
            value="📁 เปิดอยู่" if anti_nuke_status[guild_id] else "💢 ปิดอยู่",
            inline=False
        )

        await interaction.response.send_message(
            embed=embed,
            view=AntiNukeMainView(guild_id),
            ephemeral=True
        )

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel: discord.abc.GuildChannel):

        guild = channel.guild
        guild_id = guild.id

        if not anti_nuke_status.get(guild_id, False):
            return

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

        # เก็บเฉพาะใน 5 วิล่าสุด
        self.action_log[user.id] = [
            t for t in self.action_log[user.id] if now - t <= 5
        ]

        # ลบเกิน 3 ห้องใน 5 วิ = แบน
        if len(self.action_log[user.id]) >= 3:
            try:
                member = guild.get_member(user.id)
                if member:
                    await member.ban(reason="Anti-Nuke: ลบห้องเร็วเกินกำหนด")
            except Exception as e:
                print("ANTI-NUKE BAN ERROR:", e)

            self.action_log[user.id].clear()


async def setup(bot):
    await bot.add_cog(AntiNuke(bot))