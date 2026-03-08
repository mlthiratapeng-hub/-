import discord
from discord.ext import commands
from discord import app_commands
import time
import asyncio
from collections import defaultdict
from database import is_whitelisted

anti_nuke_status = {}

LIMIT = 4
TIME_WINDOW = 5


class AntiNukeToggleView(discord.ui.View):
    def __init__(self, guild_id):
        super().__init__(timeout=60)
        self.guild_id = guild_id

    @discord.ui.button(label="เปิดระบบ", style=discord.ButtonStyle.success, emoji="📁")
    async def enable(self, interaction: discord.Interaction, button: discord.ui.Button):

        anti_nuke_status[self.guild_id] = True

        embed = discord.Embed(
            title="💣 ระบบ protect-Nuke",
            description="📁 เปิดระบบเรียบร้อยแล้ว",
            color=discord.Color.green()
        )

        await interaction.response.edit_message(embed=embed, view=None)

    @discord.ui.button(label="ปิดระบบ", style=discord.ButtonStyle.danger, emoji="💢")
    async def disable(self, interaction: discord.Interaction, button: discord.ui.Button):

        anti_nuke_status[self.guild_id] = False

        embed = discord.Embed(
            title="💣 ระบบ protect-Nuke",
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
            title="💣 ตั้งค่าระบบ protect-Nuke",
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

    @app_commands.command(name="protect-nuke", description="ตั้งค่าระบบ Anti-Nuke")
    async def anti_nuke(self, interaction: discord.Interaction):

        if not interaction.guild:
            return

        guild_id = interaction.guild.id

        if guild_id not in anti_nuke_status:
            anti_nuke_status[guild_id] = False

        embed = discord.Embed(
            title="💣 ตั้งค่าระบบ protect-Nuke",
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

    async def check_limit(self, guild, user):

        if is_whitelisted(user.id):
            return

        now = time.time()

        self.action_log[user.id].append(now)

        self.action_log[user.id] = [
            t for t in self.action_log[user.id]
            if now - t <= TIME_WINDOW
        ]

        if len(self.action_log[user.id]) >= LIMIT:

            member = guild.get_member(user.id)

            if member:
                try:
                    await member.ban(reason="Anti-Nuke Protection Triggered")
                except Exception as e:
                    print("BAN ERROR:", e)

            self.action_log[user.id].clear()

    async def get_audit_user(self, guild, action):

        await asyncio.sleep(1)

        async for entry in guild.audit_logs(limit=1, action=action):
            return entry.user

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel):

        guild = channel.guild

        if not anti_nuke_status.get(guild.id, False):
            return

        user = await self.get_audit_user(guild, discord.AuditLogAction.channel_delete)

        if user:
            await self.check_limit(guild, user)

    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel):

        guild = channel.guild

        if not anti_nuke_status.get(guild.id, False):
            return

        user = await self.get_audit_user(guild, discord.AuditLogAction.channel_create)

        if user:
            await self.check_limit(guild, user)

    @commands.Cog.listener()
    async def on_guild_role_delete(self, role):

        guild = role.guild

        if not anti_nuke_status.get(guild.id, False):
            return

        user = await self.get_audit_user(guild, discord.AuditLogAction.role_delete)

        if user:
            await self.check_limit(guild, user)

    @commands.Cog.listener()
    async def on_guild_role_create(self, role):

        guild = role.guild

        if not anti_nuke_status.get(guild.id, False):
            return

        user = await self.get_audit_user(guild, discord.AuditLogAction.role_create)

        if user:
            await self.check_limit(guild, user)

    @commands.Cog.listener()
    async def on_member_ban(self, guild, user):

        if not anti_nuke_status.get(guild.id, False):
            return

        attacker = await self.get_audit_user(guild, discord.AuditLogAction.ban)

        if attacker:
            await self.check_limit(guild, attacker)

    @commands.Cog.listener()
    async def on_member_remove(self, member):

        guild = member.guild

        if not anti_nuke_status.get(guild.id, False):
            return

        attacker = await self.get_audit_user(guild, discord.AuditLogAction.kick)

        if attacker:
            await self.check_limit(guild, attacker)

    @commands.Cog.listener()
    async def on_webhooks_update(self, channel):

        guild = channel.guild

        if not anti_nuke_status.get(guild.id, False):
            return

        for action in [
            discord.AuditLogAction.webhook_create,
            discord.AuditLogAction.webhook_delete,
            discord.AuditLogAction.webhook_update
        ]:

            user = await self.get_audit_user(guild, action)

            if user:
                await self.check_limit(guild, user)

    @commands.Cog.listener()
    async def on_message(self, message):

        if not message.guild:
            return

        if not anti_nuke_status.get(message.guild.id, False):
            return

        if "@everyone" in message.content or "@here" in message.content:

            if is_whitelisted(message.author.id):
                return

            await self.check_limit(message.guild, message.author)


async def setup(bot):
    await bot.add_cog(AntiNuke(bot))