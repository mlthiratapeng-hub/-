import discord
from discord.ext import commands, tasks
from discord import app_commands
import datetime

class CheckOperation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.report_channel_id = None
        self.last_status = {}
        self.hourly_report.start()

    # ===== ใช้ได้เฉพาะแอดมิน =====
    @app_commands.command(name="check_operation", description="ตรวจสอบสถานะบอททั้งหมด")
    @app_commands.checks.has_permissions(administrator=True)
    async def check_operation(self, interaction: discord.Interaction):

        self.report_channel_id = interaction.channel.id

        embed = await self.generate_report(interaction.guild)

        await interaction.response.send_message(embed=embed)

    # ===== กัน Error ถ้าไม่ใช่แอดมิน =====
    @check_operation.error
    async def check_operation_error(self, interaction: discord.Interaction, error):
        if isinstance(error, app_commands.errors.MissingPermissions):
            await interaction.response.send_message(
                "❌ คำสั่งนี้ใช้ได้เฉพาะแอดมินเซิร์ฟเวอร์",
                ephemeral=True
            )

    # ===== สร้าง Embed =====
    async def generate_report(self, guild):

        online_bots = []
        offline_bots = []

        for member in guild.members:
            if member.bot:

                if member.status in [
                    discord.Status.online,
                    discord.Status.idle,
                    discord.Status.dnd
                ]:
                    online_bots.append(member.name)
                else:
                    offline_bots.append(member.name)

        now = datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")

        embed = discord.Embed(
            title="⚙️ Online Operation Report",
            color=discord.Color.green()
        )

        embed.add_field(
            name="🍇 Online Bots",
            value="\n".join(online_bots) if online_bots else "ไม่มี",
            inline=False
        )

        embed.add_field(
            name="🍎 Offline Bots",
            value="\n".join(offline_bots) if offline_bots else "ไม่มี",
            inline=False
        )

        embed.set_footer(text=f"รายงานเมื่อ: {now}")

        return embed

    # ===== รายงานทุก 1 ชั่วโมง =====
    @tasks.loop(hours=1)
    async def hourly_report(self):
        if not self.report_channel_id:
            return

        channel = self.bot.get_channel(self.report_channel_id)
        if not channel:
            return

        guild = channel.guild
        embed = await self.generate_report(guild)
        await channel.send(embed=embed)

    # ===== แจ้งเตือนทันทีเมื่อบอท Offline =====
    @commands.Cog.listener()
    async def on_presence_update(self, before, after):

        if not after.bot:
            return

        if not self.report_channel_id:
            return

        if before.status != discord.Status.offline and after.status == discord.Status.offline:

            channel = self.bot.get_channel(self.report_channel_id)
            if not channel:
                return

            now = datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")

            embed = discord.Embed(
                title="🚨 Bot Offline Alert",
                description=f"บอท **{after.name}** ออฟไลน์แล้ว",
                color=discord.Color.red()
            )

            embed.set_footer(text=f"แจ้งเตือนเมื่อ: {now}")

            await channel.send(embed=embed)

    @hourly_report.before_loop
    async def before_hourly_report(self):
        await self.bot.wait_until_ready()


async def setup(bot):
    await bot.add_cog(CheckOperation(bot))