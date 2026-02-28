import discord
from discord import app_commands
from discord.ext import commands, tasks
import datetime
import json
import os

GUILD_ID = 1476624073990738022
CONFIG_FILE = "check_operation_config.json"


class CheckOperation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = self.load_config()
        self.hourly_report.start()

    # =========================
    # CONFIG
    # =========================
    def load_config(self):
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, "r") as f:
                return json.load(f)
        return {}

    def save_config(self):
        with open(CONFIG_FILE, "w") as f:
            json.dump(self.config, f, indent=4)

    # =========================
    # /check_operation
    # =========================
    @app_commands.command(name="check_operation", description="ตั้งค่าระบบตรวจสอบบอท")
    @app_commands.checks.has_permissions(administrator=True)
    async def check_operation(
        self,
        interaction: discord.Interaction,
        channel: discord.TextChannel
    ):

        if interaction.guild.id != GUILD_ID:
            await interaction.response.send_message(
                "🍎 ใช้ได้เฉพาะเซิร์ฟเวอร์ที่กำหนดเท่านั้น",
                ephemeral=True
            )
            return

        self.config[str(interaction.guild.id)] = channel.id
        self.save_config()

        embed = await self.generate_report(interaction.guild)

        await interaction.response.send_message(
            f"✅ ตั้งค่าห้องเป็น {channel.mention} เรียบร้อยแล้ว",
            ephemeral=True
        )

        await channel.send(embed=embed)

    # =========================
    # สร้างรายงาน
    # =========================
    async def generate_report(self, guild):

        online = []
        offline = []

        for member in guild.members:
            if member.bot:
                if member.status == discord.Status.offline:
                    offline.append(member.name)
                else:
                    online.append(member.name)

        now = datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")

        embed = discord.Embed(
            title="📂 Check the Operation",
            color=discord.Color.blue(),
            timestamp=datetime.datetime.now()
        )

        embed.add_field(
            name=f"🟢 Online Bots ({len(online)})",
            value="\n".join(online) if online else "ไม่มี",
            inline=False
        )

        embed.add_field(
            name=f"🔴 Offline Bots ({len(offline)})",
            value="\n".join(offline) if offline else "ไม่มี",
            inline=False
        )

        embed.set_footer(text=f"รายงานเวลา {now}")

        return embed

    # =========================
    # แจ้งทันทีเมื่อสถานะเปลี่ยน
    # =========================
    @commands.Cog.listener()
    async def on_presence_update(self, before, after):

        if not after.bot:
            return

        guild = after.guild

        if guild.id != GUILD_ID:
            return

        if str(guild.id) not in self.config:
            return

        channel = guild.get_channel(self.config[str(guild.id)])
        if not channel:
            return

        now = datetime.datetime.now().strftime("%H:%M:%S")

        # OFFLINE
        if before.status != discord.Status.offline and after.status == discord.Status.offline:

            embed = discord.Embed(
                title="🚨 BOT OFFLINE",
                description=f"บอท **{after.name}** ออฟไลน์แล้ว",
                color=discord.Color.red(),
                timestamp=datetime.datetime.now()
            )

            embed.set_footer(text=f"แจ้งเวลา {now}")
            await channel.send(embed=embed)

        # ONLINE
        if before.status == discord.Status.offline and after.status != discord.Status.offline:

            embed = discord.Embed(
                title="🌿 BOT ONLINE",
                description=f"บอท **{after.name}** กลับมาออนไลน์แล้ว",
                color=discord.Color.green(),
                timestamp=datetime.datetime.now()
            )

            embed.set_footer(text=f"แจ้งเวลา {now}")
            await channel.send(embed=embed)

    # =========================
    # รายงานทุก 1 ชั่วโมง
    # =========================
    @tasks.loop(hours=1)
    async def hourly_report(self):

        await self.bot.wait_until_ready()

        guild = self.bot.get_guild(GUILD_ID)
        if not guild:
            return

        if str(guild.id) not in self.config:
            return

        channel = guild.get_channel(self.config[str(guild.id)])
        if not channel:
            return

        embed = await self.generate_report(guild)
        await channel.send(embed=embed)


async def setup(bot):
    await bot.add_cog(CheckOperation(bot))