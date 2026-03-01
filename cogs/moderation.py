import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime

class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # ==============================
    # /kick
    # ==============================
    @app_commands.command(name="kick", description="เตะสมาชิกออกจากเซิร์ฟเวอร์")
    @app_commands.checks.has_permissions(kick_members=True)
    async def kick(
        self,
        interaction: discord.Interaction,
        member: discord.Member,
        reason: str = "No reason"
    ):
        await member.kick(reason=reason)

        embed = discord.Embed(
            title="Member Kick",
            color=discord.Color.orange()
        )

        embed.add_field(
            name="🍃สมาชิก",
            value=member.mention,
            inline=False
        )

        embed.add_field(
            name="🍄ผู้ใช้คำสั่ง",
            value=interaction.user.mention,
            inline=False
        )

        embed.add_field(
            name="🚧เหตุผล",
            value=reason,
            inline=False
        )

        # 🖼 ใส่รูปโปรไฟล์คนที่โดน
        embed.set_thumbnail(url=member.display_avatar.url)

        embed.set_footer(
            text=datetime.now().strftime("%d/%m/%Y %H:%M")
        )

        await interaction.response.send_message(embed=embed)


    # ==============================
    # /ban
    # ==============================
    @app_commands.command(name="ban", description="แบนสมาชิกออกจากเซิร์ฟเวอร์")
    @app_commands.checks.has_permissions(ban_members=True)
    async def ban(
        self,
        interaction: discord.Interaction,
        member: discord.Member,
        reason: str = "No reason"
    ):
        await member.ban(reason=reason)

        embed = discord.Embed(
            title="Member Ban",
            color=discord.Color.red()
        )

        embed.add_field(
            name="🍄สมาชิก",
            value=member.mention,
            inline=False
        )

        embed.add_field(
            name="🌿ผู้ใช้คำสั่ง",
            value=interaction.user.mention,
            inline=False
        )

        embed.add_field(
            name="🌳เหตุผล",
            value=reason,
            inline=False
        )

        # 🖼 ใส่รูปโปรไฟล์คนที่โดน
        embed.set_thumbnail(url=member.display_avatar.url)

        embed.set_footer(
            text=datetime.now().strftime("%d/%m/%Y %H:%M")
        )

        await interaction.response.send_message(embed=embed)


    # ==============================
    # กันคนไม่มีสิทธิ์
    # ==============================
    @kick.error
    @ban.error
    async def permission_error(self, interaction: discord.Interaction, error):
        if isinstance(error, app_commands.MissingPermissions):
            await interaction.response.send_message(
                "🫐 คุณไม่มีสิทธิ์ใช้คำสั่งนี้",
                ephemeral=True
            )


async def setup(bot):
    await bot.add_cog(Moderation(bot))