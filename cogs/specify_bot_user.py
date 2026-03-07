import discord
from discord.ext import commands
from discord import app_commands

class ServerStats(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    async def update_stats(self, guild):

        category = discord.utils.get(guild.categories, name="SERVER STATS")

        if not category:
            return

        channels = category.channels

        all_members = guild.member_count
        bots = len([m for m in guild.members if m.bot])
        members = all_members - bots

        for channel in channels:

            if "All Members" in channel.name:
                await channel.edit(name=f"🔒 All Members: {all_members}")

            elif "Members" in channel.name:
                await channel.edit(name=f"🔒 Members: {members}")

            elif "Bots" in channel.name:
                await channel.edit(name=f"🔒 Bots: {bots}")

    @commands.Cog.listener()
    async def on_member_join(self, member):

        await self.update_stats(member.guild)

    @commands.Cog.listener()
    async def on_member_remove(self, member):

        await self.update_stats(member.guild)

    @app_commands.command(
        name="specify_bot_user",
        description="สร้างห้องแสดงจำนวนคนและบอทในเซิร์ฟเวอร์"
    )
    @app_commands.checks.has_permissions(administrator=True)

    async def specify_bot_user(self, interaction: discord.Interaction):

        guild = interaction.guild

        category = discord.utils.get(guild.categories, name="SERVER STATS")

        if category:
            await interaction.response.send_message(
                "SERVER STATS มีอยู่แล้ว",
                ephemeral=True
            )
            return

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(connect=False, view_channel=True)
        }

        category = await guild.create_category(
            "🍃 SERVER STATS",
            overwrites=overwrites
        )

        all_members = guild.member_count
        bots = len([m for m in guild.members if m.bot])
        members = all_members - bots

        await guild.create_voice_channel(
            f"🔒 All Members: {all_members}",
            category=category,
            overwrites=overwrites
        )

        await guild.create_voice_channel(
            f"🔒 Members: {members}",
            category=category,
            overwrites=overwrites
        )

        await guild.create_voice_channel(
            f"🔒 Bots: {bots}",
            category=category,
            overwrites=overwrites
        )

        await interaction.response.send_message(
            "สร้าง SERVER STATS สำเร็จ",
            ephemeral=True
        )

async def setup(bot):
    await bot.add_cog(ServerStats(bot))