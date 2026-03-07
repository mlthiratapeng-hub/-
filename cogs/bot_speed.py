import discord
from discord.ext import commands
from discord import app_commands
import psutil
import platform
import time

class BotSpeed(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.process = psutil.Process()
        self.start_time = time.time()

    @app_commands.command(name="bot_speed", description="เช็คสถานะและความเร็วของบอท")
    async def bot_speed(self, interaction: discord.Interaction):

        cpu = psutil.cpu_percent()
        ram = self.process.memory_info().rss / 1024 / 1024

        latency = round(self.bot.latency * 1000)

        # คำนวณความเร็วบอทแบบง่าย
        if latency < 100:
            speed = "⚡ เร็วมาก"
        elif latency < 200:
            speed = "🚀 เร็ว"
        elif latency < 300:
            speed = "🐢 ปานกลาง"
        else:
            speed = "🐌 ช้า"

        total_members = sum(g.member_count for g in self.bot.guilds)

        embed = discord.Embed(
            title="🕸️ Bot Status",
            description="สถานะการทำงานของบอท",
            color=discord.Color.blue()
        )

        embed.set_thumbnail(url=self.bot.user.display_avatar.url)

        embed.add_field(
            name="🖱️ CPU Usage",
            value=f"{cpu} %",
            inline=True
        )

        embed.add_field(
            name="📁 RAM",
            value=f"{ram:.2f} MB",
            inline=True
        )

        embed.add_field(
            name="🗼 Latency",
            value=f"{latency} ms",
            inline=True
        )

        embed.add_field(
            name="🏍️ ความเร็วบอท",
            value=speed,
            inline=True
        )

        embed.add_field(
            name="🌍 Servers",
            value=len(self.bot.guilds),
            inline=True
        )

        embed.add_field(
            name="🍃 Members",
            value=total_members,
            inline=True
        )

        embed.set_footer(text=f"Bot : {self.bot.user}")

        await interaction.response.send_message(embed=embed)


async def setup(bot):
    await bot.add_cog(BotSpeed(bot))