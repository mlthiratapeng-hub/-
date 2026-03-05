import discord
from discord.ext import commands
from discord import app_commands
import datetime

from database import get_log_channel,set_log_channel,remove_log
from utils.embed import log_embed


class Logs(commands.Cog):

    def __init__(self,bot):
        self.bot = bot


# -------------------
# LOG SET
# -------------------

    @app_commands.command(name="log",description="ตั้งค่าห้อง log")
    async def log(self,interaction:discord.Interaction,channel:discord.TextChannel):

        if not interaction.user.guild_permissions.administrator:

            return await interaction.response.send_message(
                "❌ Admin only",
                ephemeral=True
            )

        set_log_channel(interaction.guild.id,channel.id)

        embed = log_embed(
            "📁 Log System Enabled",
            discord.Color.green()
        )

        embed.add_field(
            name="Channel",
            value=channel.mention
        )

        await interaction.response.send_message(embed=embed)


# -------------------
# MESSAGE DELETE
# -------------------

    @commands.Cog.listener()
    async def on_message_delete(self,message):

        if not message.guild:
            return

        if message.author.bot:
            return

        log = get_log_channel(message.guild.id)

        if not log:
            return

        channel = message.guild.get_channel(log)

        embed = log_embed(
            "🗑 Message Deleted",
            discord.Color.red()
        )

        embed.add_field(
            name="User",
            value=message.author.mention
        )

        embed.add_field(
            name="Channel",
            value=message.channel.mention
        )

        embed.add_field(
            name="Content",
            value=message.content or "None",
            inline=False
        )

        await channel.send(embed=embed)


# -------------------
# MESSAGE EDIT
# -------------------

    @commands.Cog.listener()
    async def on_message_edit(self,before,after):

        if before.author.bot:
            return

        if before.content == after.content:
            return

        log = get_log_channel(before.guild.id)

        if not log:
            return

        channel = before.guild.get_channel(log)

        embed = log_embed(
            "✏️ Message Edited",
            discord.Color.orange()
        )

        embed.add_field(
            name="User",
            value=before.author.mention
        )

        embed.add_field(
            name="Before",
            value=before.content or "None",
            inline=False
        )

        embed.add_field(
            name="After",
            value=after.content or "None",
            inline=False
        )

        await channel.send(embed=embed)


# -------------------
# MEMBER JOIN
# -------------------

    @commands.Cog.listener()
    async def on_member_join(self,member):

        log = get_log_channel(member.guild.id)

        if not log:
            return

        channel = member.guild.get_channel(log)

        embed = log_embed(
            "📥 Member Joined",
            discord.Color.green()
        )

        embed.add_field(
            name="User",
            value=member.mention
        )

        embed.add_field(
            name="Created",
            value=member.created_at.strftime("%Y-%m-%d")
        )

        await channel.send(embed=embed)


# -------------------
# MEMBER LEAVE
# -------------------

    @commands.Cog.listener()
    async def on_member_remove(self,member):

        log = get_log_channel(member.guild.id)

        if not log:
            return

        channel = member.guild.get_channel(log)

        embed = log_embed(
            "📤 Member Left",
            discord.Color.dark_gray()
        )

        embed.add_field(
            name="User",
            value=str(member)
        )

        await channel.send(embed=embed)


# -------------------
# ROLE CREATE
# -------------------

    @commands.Cog.listener()
    async def on_guild_role_create(self,role):

        log = get_log_channel(role.guild.id)

        if not log:
            return

        channel = role.guild.get_channel(log)

        embed = log_embed(
            "👑 Role Created",
            discord.Color.blue()
        )

        embed.add_field(
            name="Role",
            value=role.mention
        )

        await channel.send(embed=embed)


# -------------------
# CHANNEL CREATE
# -------------------

    @commands.Cog.listener()
    async def on_guild_channel_create(self,ch):

        log = get_log_channel(ch.guild.id)

        if not log:
            return

        channel = ch.guild.get_channel(log)

        embed = log_embed(
            "📁 Channel Created",
            discord.Color.green()
        )

        embed.add_field(
            name="Channel",
            value=ch.mention
        )

        await channel.send(embed=embed)


async def setup(bot):
    await bot.add_cog(Logs(bot))