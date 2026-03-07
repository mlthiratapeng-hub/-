import discord
from discord.ext import commands
from discord import app_commands

class ServerStats(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def update_stats(self, guild: discord.Guild):

        category = discord.utils.get(guild.categories, name="🕸️ 𝗦𝗘𝗥𝗩𝗘𝗥 𝗦𝗧𝗔𝗧𝗦")

        if not category:
            return

        all_members = guild.member_count
        bots = len([m for m in guild.members if m.bot])
        members = all_members - bots

        for channel in category.channels:

            try:

                if "All Members" in channel.name:
                    await channel.edit(name=f"🔒 All Members: {all_members}")

                elif "Members" in channel.name:
                    await channel.edit(name=f"🔒 Members: {members}")

                elif "Bots" in channel.name:
                    await channel.edit(name=f"🔒 Bots: {bots}")

            except:
                pass

    @commands.Cog.listener()
    async def on_member_join(self, member):
        await self.update_stats(member.guild)

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        await self.update_stats(member.guild)

    @app_commands.command(
        name="specify_bot_user",
        description="บอกจำนวนคนและบอทในเซิร์ฟเวอร์"
    )
    async def specify_bot_user(self, interaction: discord.Interaction):

        # เช็คว่าเป็นแอดมินไหม
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message(
                "🌶️ คำสั่งนี้ใช้ได้เฉพาะแอดมิน",
                ephemeral=True
            )
            return

        guild = interaction.guild

        category = discord.utils.get(guild.categories, name="🕸️ 𝗦𝗘𝗥𝗩𝗘𝗥 𝗦𝗧𝗔𝗧𝗦")

        if category:
            await interaction.response.send_message(
                "🍅 𝗦𝗘𝗥𝗩𝗘𝗥 𝗦𝗧𝗔𝗧𝗦 ถูกสร้างไปแล้ว",
                ephemeral=True
            )
            return

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(
                connect=False,
                view_channel=True
            )
        }

        category = await guild.create_category(
            "🕸️ 𝗦𝗘𝗥𝗩𝗘𝗥 𝗦𝗧𝗔𝗧𝗦",
            overwrites=overwrites
        )

        all_members = guild.member_count
        bots = len([m for m in guild.members if m.bot])
        members = all_members - bots

        await guild.create_voice_channel(
            f"🔒 𝗔𝗟𝗟 𝗠𝗘𝗠𝗕𝗘𝗥𝗦: {all_members}",
            category=category,
            overwrites=overwrites
        )

        await guild.create_voice_channel(
            f"🔒 𝗠𝗘𝗠𝗕𝗘𝗥𝗦: {members}",
            category=category,
            overwrites=overwrites
        )

        await guild.create_voice_channel(
            f"🔒 𝗕𝗢𝗧𝗦: {bots}",
            category=category,
            overwrites=overwrites
        )

        await interaction.response.send_message(
            "🍃 สร้าง 𝗦𝗘𝗥𝗩𝗘𝗥 𝗦𝗧𝗔𝗧𝗦 สำเร็จ",
            ephemeral=True
        )


async def setup(bot):
    await bot.add_cog(ServerStats(bot))