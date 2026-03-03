import discord
from discord.ext import commands
from discord import app_commands
from datetime import timedelta


MAX_HOURS = 330


class OutOfTime(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="out_of_time",
        description="หมดเวลาสมาชิก (สูงสุด 330 ชั่วโมง)"
    )
    @app_commands.describe(
        member="สมาชิกที่ต้องการหมดเวลา",
        hours="จำนวนชั่วโมง (สูงสุด 330)",
        reason="เหตุผล"
    )
    async def out_of_time(
        self,
        interaction: discord.Interaction,
        member: discord.Member,
        hours: int,
        reason: str
    ):

        # เช็คสิทธิ์
        if not interaction.user.guild_permissions.moderate_members:
            await interaction.response.send_message(
                "🍅 คำสั่งนี้ใช้ได้เฉพาะแอดมิน/ผู้มีสิทธิ์เท่านั้น",
                ephemeral=True
            )
            return

        # เช็คจำนวนชั่วโมง
        if hours <= 0 or hours > MAX_HOURS:
            await interaction.response.send_message(
                f"🌶️ กำหนดเวลาได้สูงสุด {MAX_HOURS} ชั่วโมงเท่านั้น",
                ephemeral=True
            )
            return

        # กัน timeout ตัวเอง / เจ้าของเซิร์ฟ
        if member == interaction.user:
            await interaction.response.send_message(
                "🍒 คุณไม่สามารถหมดเวลาตัวเองได้",
                ephemeral=True
            )
            return

        if member.top_role >= interaction.user.top_role:
            await interaction.response.send_message(
                "🍎 คุณไม่สามารถหมดเวลาคนที่มียศสูงกว่าหรือเท่ากันได้",
                ephemeral=True
            )
            return

        try:
            await member.timeout(
                timedelta(hours=hours),
                reason=reason
            )
        except Exception as e:
            await interaction.response.send_message(
                f"🍇 เกิดข้อผิดพลาด: {e}",
                ephemeral=True
            )
            return

        # ===== Embed =====
        embed = discord.Embed(
            title="⏳ สมาชิกถูกหมดเวลา",
            color=discord.Color.red()
        )

        embed.set_thumbnail(url=member.display_avatar.url)

        embed.add_field(
            name="👤 ผู้ถูกหมดเวลา",
            value=f"{member.mention}\n`{member.id}`",
            inline=False
        )

        embed.add_field(
            name="👮 ผู้ใช้คำสั่ง",
            value=f"{interaction.user.mention}",
            inline=False
        )

        embed.add_field(
            name="⏰ ระยะเวลา",
            value=f"{hours} ชั่วโมง",
            inline=False
        )

        embed.add_field(
            name="📝 เหตุผล",
            value=reason,
            inline=False
        )

        embed.set_footer(text="Security Moderation System")

        await interaction.response.send_message(embed=embed)


async def setup(bot):
    await bot.add_cog(OutOfTime(bot))