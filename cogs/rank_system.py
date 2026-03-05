import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime


class RankSystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # ==========================
    # /rank ให้ยศ
    # ==========================
    @app_commands.command(
        name="rank",
        description="ให้ยศแก่บุคคล"
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def rank(
        self,
        interaction: discord.Interaction,
        member: discord.Member,
        role: discord.Role
    ):
        try:
            await member.add_roles(role)

            embed = discord.Embed(
                title="🎖️ มีการมอบยศ",
                color=discord.Color.green(),
                timestamp=datetime.utcnow()
            )

            embed.add_field(
                name="🍇 ผู้ใช้คำสั่ง",
                value=interaction.user.mention,
                inline=False
            )

            embed.add_field(
                name="👤 ผู้ได้รับยศ",
                value=member.mention,
                inline=False
            )

            embed.add_field(
                name="🏅 ยศที่ได้รับ",
                value=role.mention,
                inline=False
            )

            embed.set_thumbnail(url=member.display_avatar.url)

            await interaction.response.send_message(embed=embed)

        except Exception as e:
            await interaction.response.send_message(
                "🌶️ เกิดข้อผิดพลาด",
                ephemeral=True
            )
            print("RANK ERROR:", e)

    # ==========================
    # /release ปลดยศ
    # ==========================
    @app_commands.command(
        name="release",
        description="ปลดยศ"
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def release(
        self,
        interaction: discord.Interaction,
        member: discord.Member,
        role: discord.Role,
        reason: str
    ):
        try:
            await member.remove_roles(role)

            embed = discord.Embed(
                title="🕸️ มีการปลดยศ",
                color=discord.Color.red(),
                timestamp=datetime.utcnow()
            )

            embed.add_field(
                name="🍇 ผู้ใช้คำสั่ง",
                value=interaction.user.mention,
                inline=False
            )

            embed.add_field(
                name="👤 ผู้ถูกปลด",
                value=member.mention,
                inline=False
            )

            embed.add_field(
                name="🏅 ยศที่ถูกปลด",
                value=role.mention,
                inline=False
            )

            embed.add_field(
                name="📂 เหตุผล",
                value=reason,
                inline=False
            )

            embed.set_thumbnail(url=member.display_avatar.url)

            await interaction.response.send_message(embed=embed)

        except Exception as e:
            await interaction.response.send_message(
                "🍅 เกิดข้อผิดพลาด",
                ephemeral=True
            )
            print("RELEASE ERROR:", e)


async def setup(bot):
    await bot.add_cog(RankSystem(bot))