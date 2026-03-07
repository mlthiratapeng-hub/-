import discord
from discord import app_commands
from discord.ext import commands, tasks
import json
import os
from datetime import datetime

CONFIG_FILE = "operation_channels.json"


class CheckOperation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.operation_channels = self.load_config()

    def load_config(self):
        if not os.path.exists(CONFIG_FILE):
            return {}
        try:
            with open(CONFIG_FILE, "r") as f:
                return json.load(f)
        except:
            return {}

    def save_config(self):
        with open(CONFIG_FILE, "w") as f:
            json.dump(self.operation_channels, f, indent=4)

    # -------------------------
    # สร้างรายงานสถานะบอท
    # -------------------------
    async def generate_report(self, guild: discord.Guild):

        online = []
        offline = []

        for member in guild.members:
            if member.bot:
                if member.status == discord.Status.offline:
                    offline.append(member)
                else:
                    online.append(member)

        # แสดงชื่อบอทแทน mention
        online_names = "\n".join([f"@{bot.display_name}" for bot in online]) or "None"
        offline_names = "\n".join([f"@{bot.display_name}" for bot in offline]) or "None"

        embed = discord.Embed(
            title="📁 Bot Operation Report",
            color=discord.Color.blue(),
            timestamp=datetime.utcnow()
        )

        embed.add_field(
            name="🟢 Online Bots",
            value=online_names,
            inline=False
        )

        embed.add_field(
            name="🔴 Offline Bots",
            value=offline_names,
            inline=False
        )

        embed.set_footer(
            text=f"Total Bots: {len(online) + len(offline)} | วันนี้ เวลา {datetime.now().strftime('%H:%M')}"
        )

        return embed

    # -------------------------
    # Slash Command
    # -------------------------
    @app_commands.command(name="check_operation", description="เช็คการทำงานของบอททั้งเซิฟ")
    @app_commands.checks.has_permissions(administrator=True)
    async def check_operation(self, interaction: discord.Interaction, channel: discord.TextChannel):

        self.operation_channels[str(interaction.guild.id)] = channel.id
        self.save_config()

        embed = await self.generate_report(interaction.guild)

        await interaction.response.send_message("🍃 ตั้งค่าห้องเรียบร้อย", ephemeral=True)
        await channel.send(embed=embed)

    # -------------------------
    # แจ้งเมื่อสถานะบอทเปลี่ยน
    # -------------------------
    @commands.Cog.listener()
    async def on_presence_update(self, before, after):

        if not after.bot:
            return

        if before.status == after.status:
            return

        guild = after.guild
        if str(guild.id) not in self.operation_channels:
            return

        channel_id = self.operation_channels[str(guild.id)]
        channel = guild.get_channel(channel_id)

        if not channel:
            return

        status_text = "🟢 ONLINE" if after.status != discord.Status.offline else "🔴 OFFLINE"

        embed = discord.Embed(
            title="⚠ Bot Status Changed",
            description=f"@{after.display_name} is now {status_text}",
            color=discord.Color.green() if after.status != discord.Status.offline else discord.Color.red(),
            timestamp=datetime.utcnow()
        )

        await channel.send(embed=embed)

    # -------------------------
    # รายงานทุก 1 ชั่วโมง
    # -------------------------
    @tasks.loop(hours=1)
    async def hourly_report(self):

        for guild_id, channel_id in self.operation_channels.items():

            guild = self.bot.get_guild(int(guild_id))
            if not guild:
                continue

            channel = guild.get_channel(channel_id)
            if not channel:
                continue

            embed = await self.generate_report(guild)
            await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_ready(self):

        if not self.hourly_report.is_running():
            self.hourly_report.start()


async def setup(bot):
    await bot.add_cog(CheckOperation(bot))