import discord
from discord.ext import commands, tasks
from discord import app_commands
import datetime
import json
import os


CONFIG_FILE = "monitor_config.json"


def load_config():
    if not os.path.exists(CONFIG_FILE):
        return {}
    with open(CONFIG_FILE, "r") as f:
        return json.load(f)


def save_config(data):
    with open(CONFIG_FILE, "w") as f:
        json.dump(data, f, indent=4)


class CheckOperation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = load_config()
        self.hourly_report.start()

    # ===== Slash Command (Admin Only) =====
    @app_commands.command(
        name="check_operation",
        description="ตั้งค่าช่องรายงานสถานะบอท"
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def check_operation(self, interaction: discord.Interaction):

        guild_id = str(interaction.guild.id)
        self.config[guild_id] = interaction.channel.id
        save_config(self.config)

        await interaction.response.send_message(
            "🍃 ตั้งค่าช่องรายงานเรียบร้อยแล้ว",
            ephemeral=True
        )

    # ===== Error ถ้าไม่ใช่แอดมิน =====
    @check_operation.error
    async def check_operation_error(self, interaction: discord.Interaction, error):
        if isinstance(error, app_commands.errors.MissingPermissions):
            await interaction.response.send_message(
                "🌶️ คำสั่งนี้ใช้ได้เฉพาะแอดมิน",
                ephemeral=True
            )

    # ===== สร้าง Embed =====
    async def generate_report(self, guild):

        online_bots = []
        offline_bots = []

        for member in guild.members:
            if member.bot:
                if member.status == discord.Status.offline:
                    offline_bots.append(member.name)
                else:
                    online_bots.append(member.name)

        now = datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")

        embed = discord.Embed(
            title="⚙ Online Operation Report",
            color=discord.Color.green()
        )

        embed.add_field(
            name="🍏 Online Bots",
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

        for guild in self.bot.guilds:

            guild_id = str(guild.id)

            if guild_id not in self.config:
                continue

            channel_id = self.config[guild_id]
            channel = guild.get_channel(channel_id)

            if not channel:
                continue

            embed = await self.generate_report(guild)
            await channel.send(embed=embed)

    @hourly_report.before_loop
    async def before_hourly_report(self):
        await self.bot.wait_until_ready()

    # ===== แจ้งเตือนทันทีเมื่อบอท Offline =====
    @commands.Cog.listener()
    async def on_presence_update(self, before, after):

        if not after.bot:
            return

        if before.status != discord.Status.offline and after.status == discord.Status.offline:

            guild_id = str(after.guild.id)

            if guild_id not in self.config:
                return

            channel_id = self.config[guild_id]
            channel = after.guild.get_channel(channel_id)

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


async def setup(bot):
    await bot.add_cog(CheckOperation(bot))