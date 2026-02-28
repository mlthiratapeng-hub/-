import discord
from discord import app_commands
from discord.ext import commands, tasks
import datetime
import json
import os

CONFIG_FILE = "check_operation_config.json"


class CheckOperation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = self.load_config()
        self.hourly_report.start()

    # =========================
    # โหลด / บันทึก config
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
    # คำสั่งตั้งค่าช่อง
    # =========================
    @app_commands.command(name="set_monitor_channel", description="ตั้งค่าช่องแจ้งเตือนบอท")
    @app_commands.checks.has_permissions(administrator=True)
    async def set_monitor_channel(self, interaction: discord.Interaction, channel: discord.TextChannel):

        guild_id = str(interaction.guild.id)
        self.config[guild_id] = channel.id
        self.save_config()

        await interaction.response.send_message(
            f"🍇 ตั้งค่าช่องแจ้งเตือนเป็น {channel.mention} เรียบร้อยแล้ว",
            ephemeral=True
        )

    # =========================
    # คำสั่งหลัก
    # =========================
    @app_commands.command(name="check_operation", description="ตรวจสอบสถานะบอททั้งหมด")
    @app_commands.checks.has_permissions(administrator=True)
    async def check_operation(self, interaction: discord.Interaction):

        embed = await self.generate_report(interaction.guild)
        await interaction.response.send_message(embed=embed)

    # =========================
    # สร้างรายงาน
    # =========================
    async def generate_report(self, guild):

        online_bots = []
        offline_bots = []

        for member in guild.members:
            if member.bot:
                if member.status == discord.Status.offline:
                    offline_bots.append(member.name)
                else:
                    online_bots.append(member.name)

        embed = discord.Embed(
            title="📂 Check the Operation",
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

    # =========================
    # แจ้งเตือนทันทีเมื่อสถานะเปลี่ยน
    # =========================
    @commands.Cog.listener()
    async def on_presence_update(self, before, after):

        if not after.bot:
            return

        guild = after.guild
        guild_id = str(guild.id)

        if guild_id not in self.config:
            return

        channel_id = self.config[guild_id]
        channel = guild.get_channel(channel_id)

        if not channel:
            return

        now = datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")

        # ===== OFFLINE =====
        if before.status != discord.Status.offline and after.status == discord.Status.offline:

            embed = discord.Embed(
                title="🚨 BOT OFFLINE",
                description=f"บอท **{after.name}** ออฟไลน์แล้ว!",
                color=discord.Color.red()
            )

            embed.set_footer(text=f"แจ้งเตือนเมื่อ: {now}")
            await channel.send(embed=embed)

        # ===== ONLINE =====
        if before.status == discord.Status.offline and after.status != discord.Status.offline:

            embed = discord.Embed(
                title="🌿 BOT ONLINE",
                description=f"บอท **{after.name}** กลับมาออนไลน์แล้ว!",
                color=discord.Color.green()
            )

            embed.set_footer(text=f"แจ้งเตือนเมื่อ: {now}")
            await channel.send(embed=embed)

    # =========================
    # รายงานทุก 1 ชั่วโมง
    # =========================
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


async def setup(bot):
    await bot.add_cog(CheckOperation(bot))