import discord
from discord import app_commands
from discord.ext import commands, tasks

class CheckOperation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.auto_channel_id = None
        self.auto_guild_id = None

    # ==============================
    # ฟังก์ชันเช็คบอท
    # ==============================
    async def generate_report(self, guild: discord.Guild):
        online_bots = []
        offline_bots = []

        for member in guild.members:
            if member.bot:
                if member.status == discord.Status.offline:
                    offline_bots.append(member.name)
                else:
                    online_bots.append(member.name)

        embed = discord.Embed(
            title="📁 Check the Operation",
            color=discord.Color.blue()
        )

        embed.add_field(
            name="🟢 Online Bots",
            value="\n".join(online_bots) if online_bots else "ไม่มี",
            inline=False
        )

        embed.add_field(
            name="🔴 Offline Bots",
            value="\n".join(offline_bots) if offline_bots else "ไม่มี",
            inline=False
        )

        embed.set_footer(text="Bot Monitoring System")

        return embed

    # ==============================
    # Slash Command
    # ==============================
    @app_commands.command(
        name="check_operation",
        description="ตรวจสอบว่าบอทในเซิร์ฟออนไลน์กี่ตัว"
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def check_operation(
        self,
        interaction: discord.Interaction,
        channel: discord.TextChannel
    ):
        guild = interaction.guild

        embed = await self.generate_report(guild)

        await channel.send(embed=embed)
        await interaction.response.send_message(
            "✅ ตั้งค่าห้องรายงานอัตโนมัติแล้ว (ทุก 1 ชั่วโมง)",
            ephemeral=True
        )

        # เก็บค่าห้องไว้สำหรับ auto
        self.auto_channel_id = channel.id
        self.auto_guild_id = guild.id

        if not self.auto_report.is_running():
            self.auto_report.start()

    # ==============================
    # Auto Report ทุก 1 ชั่วโมง
    # ==============================
    @tasks.loop(hours=1)
    async def auto_report(self):
        if not self.auto_channel_id or not self.auto_guild_id:
            return

        guild = self.bot.get_guild(self.auto_guild_id)
        channel = self.bot.get_channel(self.auto_channel_id)

        if guild and channel:
            embed = await self.generate_report(guild)
            await channel.send(embed=embed)

    @auto_report.before_loop
    async def before_auto_report(self):
        await self.bot.wait_until_ready()

# ==============================
# Setup
# ==============================
async def setup(bot):
    await bot.add_cog(CheckOperation(bot))