import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime

class ServerInfo(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # ================= TIME FORMAT =================
    def format_time_ago(self, created_at: datetime):
        now = datetime.utcnow()
        delta = now - created_at.replace(tzinfo=None)

        total_days = delta.days

        years = total_days // 365
        remaining_days = total_days % 365

        months = remaining_days // 30
        days = remaining_days % 30

        parts = []

        if years > 0:
            parts.append(f"{years} ปี")
        if months > 0:
            parts.append(f"{months} เดือน")
        if days > 0:
            parts.append(f"{days} วัน")

        if not parts:
            parts.append("ไม่ถึง 1 วัน")

        return " ".join(parts) + " ที่แล้ว"

    # ================= COMMAND =================
    @app_commands.command(name="server", description="ดูข้อมูลเซิร์ฟเวอร์")
    async def server(self, interaction: discord.Interaction):

        guild = interaction.guild

        if guild is None:
            await interaction.response.send_message("ใช้ได้เฉพาะในเซิร์ฟเวอร์เท่านั้น", ephemeral=True)
            return

        await interaction.response.defer()

        # ===== สมาชิก =====
        humans = len([m for m in guild.members if not m.bot])
        bots = len([m for m in guild.members if m.bot])

        # ===== ช่อง =====
        text_channels = len(guild.text_channels)
        voice_channels = len(guild.voice_channels)
        categories = len(guild.categories)

        # ===== วันสร้าง =====
        created_at = guild.created_at
        time_ago = self.format_time_ago(created_at)

        # ===== Embed =====
        embed = discord.Embed(
            title="ข้อมูลเซิร์ฟเวอร์",
            color=discord.Color.from_rgb(0, 0, 0),  # 🔥 เส้นสีดำ
            timestamp=datetime.utcnow()
        )

        embed.add_field(name="ชื่อเซิร์ฟเวอร์", value=guild.name, inline=False)
        embed.add_field(name="ไอดีเซิร์ฟเวอร์", value=guild.id, inline=False)
        embed.add_field(name="เจ้าของเซิร์ฟเวอร์", value=str(guild.owner), inline=False)

        embed.add_field(
            name="สร้างเมื่อ",
            value=f"{created_at.strftime('%d/%m/%Y %H:%M')} ({time_ago})",
            inline=False
        )

        embed.add_field(
            name=f"สมาชิก [ {guild.member_count} ]",
            value=f"คน: {humans} | บอท: {bots}",
            inline=False
        )

        embed.add_field(
            name=f"ช่อง [ {text_channels + voice_channels + categories} ]",
            value=f"ข้อความ: {text_channels} | เสียง: {voice_channels} | หมวดหมู่: {categories}",
            inline=False
        )

        embed.add_field(
            name="การบูสต์",
            value=f"{guild.premium_subscription_count} (ระดับ {guild.premium_tier})",
            inline=False
        )

        embed.add_field(
            name=f"บทบาท [ {len(guild.roles)} ]",
            value=", ".join(role.name for role in guild.roles[-15:]) if guild.roles else "ไม่มี",
            inline=False
        )

        # รูปโปรไฟล์เซิร์ฟ
        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)

        await interaction.followup.send(embed=embed)


async def setup(bot):
    await bot.add_cog(ServerInfo(bot))