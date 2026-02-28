import discord
from discord import app_commands
from discord.ext import commands, tasks

class CheckOperation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.auto_channel_id = None
        self.auto_guild_id = None
        self.last_status = {}  # เก็บสถานะล่าสุดของบอท

    # ==============================
    # สร้างรายงาน
    # ==============================
    async def generate_report(self, guild: discord.Guild):
        online_bots = []
        offline_bots = []

        for member in guild.members:
            if member.bot:
                self.last_status.setdefault(member.id, member.status)

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
        description="ตรวจสอบและตั้งค่าระบบตรวจบอท"
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
            "🍃 เปิดระบบตรวจบอท + แจ้งเตือนทันทีแล้ว",
            ephemeral=True
        )

        self.auto_channel_id = channel.id
        self.auto_guild_id = guild.id

        if not self.auto_report.is_running():
            self.auto_report.start()

    # ==============================
    # แจ้งเตือนทันทีเมื่อสถานะเปลี่ยน
    # ==============================
    @commands.Cog.listener()
    async def on_presence_update(self, before, after):
        if not after.bot:
            return

        if not self.auto_channel_id:
            return

        old_status = self.last_status.get(after.id)
        new_status = after.status

        if old_status != new_status:
            self.last_status[after.id] = new_status

            channel = self.bot.get_channel(self.auto_channel_id)
            if not channel:
                return

            if new_status == discord.Status.offline:
                embed = discord.Embed(
                    title="🚨 BOT OFFLINE",
                    description=f"บอท **{after.name}** ออฟไลน์แล้ว!",
                    color=discord.Color.red()
                )
                await channel.send(embed=embed)

            elif old_status == discord.Status.offline and new_status != discord.Status.offline:
                embed = discord.Embed(
                    title="🍃 BOT ONLINE",
                    description=f"บอท **{after.name}** กลับมาออนไลน์แล้ว!",
                    color=discord.Color.green()
                )
                await channel.send(embed=embed)

    # ==============================
    # รายงานทุก 1 ชั่วโมง
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