import discord
from discord.ext import commands
from discord import app_commands
import sqlite3
import datetime

DB = "data.db"


# ==============================
# DATABASE
# ==============================

def get_log_channel(guild_id):
    conn = sqlite3.connect(DB)
    c = conn.cursor()

    c.execute("SELECT channel_id FROM logs WHERE guild_id=?", (guild_id,))
    result = c.fetchone()

    conn.close()

    if result:
        return result[0]
    return None


def set_log_channel(guild_id, channel_id):
    conn = sqlite3.connect(DB)
    c = conn.cursor()

    c.execute(
        "INSERT OR REPLACE INTO logs (guild_id, channel_id) VALUES (?,?)",
        (guild_id, channel_id)
    )

    conn.commit()
    conn.close()


# ==============================
# COG
# ==============================

class Logs(commands.Cog):
    def __init__(self, bot):
        self.bot = bot


# ==============================
# /logall
# ==============================

    @app_commands.command(name="logall", description="ตั้งค่าห้อง Log")
    async def logall(self, interaction: discord.Interaction, channel: discord.TextChannel):

        if not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message(
                "💢 Admin เท่านั้น",
                ephemeral=True
            )

        set_log_channel(interaction.guild.id, channel.id)

        await interaction.response.send_message(
            f"📁 ตั้งค่าห้อง Log เป็น {channel.mention} แล้ว",
            ephemeral=True
        )


# ==============================
# MESSAGE DELETE
# ==============================

    @commands.Cog.listener()
    async def on_message_delete(self, message):

        if not message.guild or message.author.bot:
            return

        channel_id = get_log_channel(message.guild.id)
        if not channel_id:
            return

        log_channel = message.guild.get_channel(channel_id)
        if not log_channel:
            return

        embed = discord.Embed(
            title="🗑 Message Deleted",
            color=discord.Color.red(),
            timestamp=datetime.datetime.utcnow()
        )

        embed.add_field(name="User", value=message.author.mention, inline=False)
        embed.add_field(name="Channel", value=message.channel.mention, inline=False)
        embed.add_field(name="Content", value=message.content or "No Text", inline=False)

        await log_channel.send(embed=embed)


# ==============================
# MESSAGE EDIT
# ==============================

    @commands.Cog.listener()
    async def on_message_edit(self, before, after):

        if not before.guild or before.author.bot:
            return

        if before.content == after.content:
            return

        channel_id = get_log_channel(before.guild.id)
        if not channel_id:
            return

        log_channel = before.guild.get_channel(channel_id)

        embed = discord.Embed(
            title="✏️ Message Edited",
            color=discord.Color.orange(),
            timestamp=datetime.datetime.utcnow()
        )

        embed.add_field(name="User", value=before.author.mention, inline=False)
        embed.add_field(name="Channel", value=before.channel.mention, inline=False)
        embed.add_field(name="Before", value=before.content or "None", inline=False)
        embed.add_field(name="After", value=after.content or "None", inline=False)

        await log_channel.send(embed=embed)


# ==============================
# MEMBER JOIN
# ==============================

    @commands.Cog.listener()
    async def on_member_join(self, member):

        channel_id = get_log_channel(member.guild.id)
        if not channel_id:
            return

        log_channel = member.guild.get_channel(channel_id)

        embed = discord.Embed(
            title="📥 Member Joined",
            color=discord.Color.green(),
            timestamp=datetime.datetime.utcnow()
        )

        embed.add_field(name="User", value=member.mention)
        embed.add_field(name="Account Created", value=member.created_at.strftime("%Y-%m-%d"))

        await log_channel.send(embed=embed)


# ==============================
# MEMBER LEAVE
# ==============================

    @commands.Cog.listener()
    async def on_member_remove(self, member):

        channel_id = get_log_channel(member.guild.id)
        if not channel_id:
            return

        log_channel = member.guild.get_channel(channel_id)

        embed = discord.Embed(
            title="📤 Member Left",
            color=discord.Color.dark_gray(),
            timestamp=datetime.datetime.utcnow()
        )

        embed.add_field(name="User", value=member.name)

        await log_channel.send(embed=embed)


# ==============================
# MEMBER UPDATE
# ==============================

    @commands.Cog.listener()
    async def on_member_update(self, before, after):

        if before.nick != after.nick:

            channel_id = get_log_channel(before.guild.id)
            if not channel_id:
                return

            log_channel = before.guild.get_channel(channel_id)

            embed = discord.Embed(
                title="📝 Nickname Changed",
                color=discord.Color.blue(),
                timestamp=datetime.datetime.utcnow()
            )

            embed.add_field(name="User", value=before.mention)
            embed.add_field(name="Before", value=before.nick)
            embed.add_field(name="After", value=after.nick)

            await log_channel.send(embed=embed)


# ==============================
# ROLE UPDATE
# ==============================

        if before.roles != after.roles:

            channel_id = get_log_channel(before.guild.id)
            if not channel_id:
                return

            log_channel = before.guild.get_channel(channel_id)

            before_roles = set(before.roles)
            after_roles = set(after.roles)

            added = after_roles - before_roles
            removed = before_roles - after_roles

            if added:
                for role in added:
                    embed = discord.Embed(
                        title="➕ Role Added",
                        color=discord.Color.green()
                    )
                    embed.add_field(name="User", value=after.mention)
                    embed.add_field(name="Role", value=role.mention)
                    await log_channel.send(embed=embed)

            if removed:
                for role in removed:
                    embed = discord.Embed(
                        title="➖ Role Removed",
                        color=discord.Color.red()
                    )
                    embed.add_field(name="User", value=after.mention)
                    embed.add_field(name="Role", value=role.mention)
                    await log_channel.send(embed=embed)


# ==============================
# CHANNEL CREATE
# ==============================

    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel):

        channel_id = get_log_channel(channel.guild.id)
        if not channel_id:
            return

        log_channel = channel.guild.get_channel(channel_id)

        embed = discord.Embed(
            title="📁 Channel Created",
            color=discord.Color.green()
        )

        embed.add_field(name="Channel", value=channel.name)

        await log_channel.send(embed=embed)


# ==============================
# CHANNEL DELETE
# ==============================

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel):

        channel_id = get_log_channel(channel.guild.id)
        if not channel_id:
            return

        log_channel = channel.guild.get_channel(channel_id)

        embed = discord.Embed(
            title="🗑 Channel Deleted",
            color=discord.Color.red()
        )

        embed.add_field(name="Channel", value=channel.name)

        await log_channel.send(embed=embed)


# ==============================
# BAN
# ==============================

    @commands.Cog.listener()
    async def on_member_ban(self, guild, user):

        channel_id = get_log_channel(guild.id)
        if not channel_id:
            return

        log_channel = guild.get_channel(channel_id)

        embed = discord.Embed(
            title="🔨 User Banned",
            color=discord.Color.red()
        )

        embed.add_field(name="User", value=str(user))

        await log_channel.send(embed=embed)


# ==============================
# UNBAN
# ==============================

    @commands.Cog.listener()
    async def on_member_unban(self, guild, user):

        channel_id = get_log_channel(guild.id)
        if not channel_id:
            return

        log_channel = guild.get_channel(channel_id)

        embed = discord.Embed(
            title="🔓 User Unbanned",
            color=discord.Color.green()
        )

        embed.add_field(name="User", value=str(user))

        await log_channel.send(embed=embed)


async def setup(bot):
    await bot.add_cog(Logs(bot))