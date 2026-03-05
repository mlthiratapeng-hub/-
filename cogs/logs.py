import discord
from discord.ext import commands
from discord import app_commands

class Logs(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.log_channels = {}

    def get_log(self, guild):
        channel_id = self.log_channels.get(guild.id)
        if not channel_id:
            return None
        return guild.get_channel(channel_id)

    # =================
    # /logall
    # =================

    @app_commands.command(name="logall", description="ตั้งค่าห้อง log")
    async def logall(self, interaction: discord.Interaction, channel: discord.TextChannel):

        if not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message(
                "❌ Admin only", ephemeral=True
            )

        self.log_channels[interaction.guild.id] = channel.id

        embed = discord.Embed(
            title="📁 ตั้งค่าห้อง Log สำเร็จ",
            description=f"Log channel = {channel.mention}",
            color=discord.Color.green()
        )

        await interaction.response.send_message(embed=embed, ephemeral=True)

    # =================
    # message delete
    # =================

    @commands.Cog.listener()
    async def on_message_delete(self, message):

        if not message.guild or message.author.bot:
            return

        log = self.get_log(message.guild)
        if not log:
            return

        embed = discord.Embed(
            title="🗑 Message Delete",
            color=discord.Color.red()
        )

        embed.add_field(name="User", value=message.author.mention)
        embed.add_field(name="Channel", value=message.channel.mention)
        embed.add_field(name="Message", value=message.content or "None")

        embed.set_thumbnail(url=message.author.display_avatar.url)

        await log.send(embed=embed)

    # =================
    # message edit
    # =================

    @commands.Cog.listener()
    async def on_message_edit(self, before, after):

        if not before.guild:
            return

        if before.content == after.content:
            return

        log = self.get_log(before.guild)
        if not log:
            return

        embed = discord.Embed(
            title="✏️ Message Edit",
            color=discord.Color.orange()
        )

        embed.add_field(name="User", value=before.author.mention)
        embed.add_field(name="Before", value=before.content or "None", inline=False)
        embed.add_field(name="After", value=after.content or "None", inline=False)

        embed.set_thumbnail(url=before.author.display_avatar.url)

        await log.send(embed=embed)

    # =================
    # member join
    # =================

    @commands.Cog.listener()
    async def on_member_join(self, member):

        log = self.get_log(member.guild)
        if not log:
            return

        embed = discord.Embed(
            title="📥 Member Join",
            description=f"{member.mention} joined the server",
            color=discord.Color.green()
        )

        embed.set_thumbnail(url=member.display_avatar.url)

        await log.send(embed=embed)

    # =================
    # member leave
    # =================

    @commands.Cog.listener()
    async def on_member_remove(self, member):

        log = self.get_log(member.guild)
        if not log:
            return

        embed = discord.Embed(
            title="📤 Member Leave",
            description=f"{member.name} left the server",
            color=discord.Color.red()
        )

        embed.set_thumbnail(url=member.display_avatar.url)

        await log.send(embed=embed)

    # =================
    # ban
    # =================

    @commands.Cog.listener()
    async def on_member_ban(self, guild, user):

        log = self.get_log(guild)
        if not log:
            return

        embed = discord.Embed(
            title="🔨 User Banned",
            description=f"{user}",
            color=discord.Color.dark_red()
        )

        embed.set_thumbnail(url=user.display_avatar.url)

        await log.send(embed=embed)

    # =================
    # unban
    # =================

    @commands.Cog.listener()
    async def on_member_unban(self, guild, user):

        log = self.get_log(guild)
        if not log:
            return

        embed = discord.Embed(
            title="🔓 User Unbanned",
            description=f"{user}",
            color=discord.Color.green()
        )

        embed.set_thumbnail(url=user.display_avatar.url)

        await log.send(embed=embed)

    # =================
    # role create
    # =================

    @commands.Cog.listener()
    async def on_guild_role_create(self, role):

        log = self.get_log(role.guild)
        if not log:
            return

        embed = discord.Embed(
            title="👑 Role Created",
            description=f"{role.name}",
            color=discord.Color.blue()
        )

        await log.send(embed=embed)

    # =================
    # role delete
    # =================

    @commands.Cog.listener()
    async def on_guild_role_delete(self, role):

        log = self.get_log(role.guild)
        if not log:
            return

        embed = discord.Embed(
            title="👑 Role Deleted",
            description=f"{role.name}",
            color=discord.Color.red()
        )

        await log.send(embed=embed)

    # =================
    # channel create
    # =================

    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel):

        log = self.get_log(channel.guild)
        if not log:
            return

        embed = discord.Embed(
            title="📁 Channel Created",
            description=channel.name,
            color=discord.Color.green()
        )

        await log.send(embed=embed)

    # =================
    # Kick log
    # =================

    @commands.Cog.listener()
    async def on_member_remove(self, member):

        log = self.get_log(member.guild)
        if not log:
            return

        try:
            async for entry in member.guild.audit_logs(limit=1, action=discord.AuditLogAction.kick):
                if entry.target.id == member.id:

                    embed = discord.Embed(
                        title="🍇 Member Kick",
                        color=discord.Color.orange()
                    )

                    embed.add_field(name="User", value=member.mention)
                    embed.add_field(name="Moderator", value=entry.user.mention)

                    embed.set_thumbnail(url=member.display_avatar.url)

                    await log.send(embed=embed)
                    return
        except:
            pass

    # =================
    # Role add/remove
    # =================

    @commands.Cog.listener()
    async def on_member_update(self, before, after):

        log = self.get_log(after.guild)
        if not log:
            return

        before_roles = set(before.roles)
        after_roles = set(after.roles)

        added = after_roles - before_roles
        removed = before_roles - after_roles

        if added:
            role = added.pop()

            embed = discord.Embed(
                title="🧾 Role Added",
                color=discord.Color.green()
            )

            embed.add_field(name="User", value=after.mention)
            embed.add_field(name="Role", value=role.mention)

            embed.set_thumbnail(url=after.display_avatar.url)

            await log.send(embed=embed)

        if removed:
            role = removed.pop()

            embed = discord.Embed(
                title="🧾 Role Removed",
                color=discord.Color.red()
            )

            embed.add_field(name="User", value=after.mention)
            embed.add_field(name="Role", value=role.mention)

            embed.set_thumbnail(url=after.display_avatar.url)

            await log.send(embed=embed)

        if before.nick != after.nick:

            embed = discord.Embed(
                title="🪪 Nickname Changed",
                color=discord.Color.blurple()
            )

            embed.add_field(name="User", value=after.mention)
            embed.add_field(name="Before", value=before.nick or "None")
            embed.add_field(name="After", value=after.nick or "None")

            embed.set_thumbnail(url=after.display_avatar.url)

            await log.send(embed=embed)

    # =================
    # Role update
    # =================

    @commands.Cog.listener()
    async def on_guild_role_update(self, before, after):

        log = self.get_log(after.guild)
        if not log:
            return

        embed = discord.Embed(
            title="👑 Role Updated",
            color=discord.Color.gold()
        )

        embed.add_field(name="Role", value=after.name)

        await log.send(embed=embed)

    # =================
    # Channel update
    # =================

    @commands.Cog.listener()
    async def on_guild_channel_update(self, before, after):

        log = self.get_log(after.guild)
        if not log:
            return

        embed = discord.Embed(
            title="📁 Channel Updated",
            color=discord.Color.blurple()
        )

        embed.add_field(name="Before", value=before.name)
        embed.add_field(name="After", value=after.name)

        await log.send(embed=embed)

    # =================
    # Emoji create
    # =================

    @commands.Cog.listener()
    async def on_guild_emojis_update(self, guild, before, after):

        log = self.get_log(guild)
        if not log:
            return

        if len(after) > len(before):

            embed = discord.Embed(
                title="🥡 Emoji Created",
                color=discord.Color.green()
            )

            await log.send(embed=embed)

        elif len(before) > len(after):

            embed = discord.Embed(
                title="🌶️ Emoji Deleted",
                color=discord.Color.red()
            )

            await log.send(embed=embed)

    # =================
    # Invite create
    # =================

    @commands.Cog.listener()
    async def on_invite_create(self, invite):

        log = self.get_log(invite.guild)
        if not log:
            return

        embed = discord.Embed(
            title="🔗 Invite Created",
            color=discord.Color.green()
        )

        embed.add_field(name="Code", value=invite.code)
        embed.add_field(name="Creator", value=invite.inviter)

        await log.send(embed=embed)

    # =================
    # Invite delete
    # =================

    @commands.Cog.listener()
    async def on_invite_delete(self, invite):

        log = self.get_log(invite.guild)
        if not log:
            return

        embed = discord.Embed(
            title="🔗 Invite Deleted",
            color=discord.Color.red()
        )

        embed.add_field(name="Code", value=invite.code)

        await log.send(embed=embed)

    # =================
    # Server icon change
    # =================

    @commands.Cog.listener()
    async def on_guild_update(self, before, after):

        log = self.get_log(after)
        if not log:
            return

        if before.icon != after.icon:

            embed = discord.Embed(
                title="🖼 Server Icon Changed",
                color=discord.Color.blurple()
            )

            embed.set_thumbnail(url=after.icon.url if after.icon else None)

            await log.send(embed=embed)

    # =================
    # channel delete
    # =================

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel):

        log = self.get_log(channel.guild)
        if not log:
            return

        embed = discord.Embed(
            title="📁 Channel Deleted",
            description=channel.name,
            color=discord.Color.red()
        )

        await log.send(embed=embed)

    # =================
    # voice join leave
    # =================

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):

        log = self.get_log(member.guild)
        if not log:
            return

        if before.channel is None and after.channel is not None:

            embed = discord.Embed(
                title="🔊 Voice Join",
                description=f"{member.mention} joined {after.channel}",
                color=discord.Color.green()
            )

        elif before.channel is not None and after.channel is None:

            embed = discord.Embed(
                title="🔊 Voice Leave",
                description=f"{member.mention} left {before.channel}",
                color=discord.Color.red()
            )

        else:

            embed = discord.Embed(
                title="🔊 Voice Move",
                description=f"{member.mention} moved {before.channel} → {after.channel}",
                color=discord.Color.orange()
            )

        embed.set_thumbnail(url=member.display_avatar.url)

        await log.send(embed=embed)


async def setup(bot):
    await bot.add_cog(Logs(bot))