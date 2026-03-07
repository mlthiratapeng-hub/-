import discord
from discord.ext import commands
from discord import app_commands
import psutil

class BotSpeed(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.process = psutil.Process()

    @app_commands.command(
        name="bot_speed",
        description="เช็คสถานะและความเร็วของบอท"
    )
    async def bot_speed(self, interaction: discord.Interaction):

        cpu = psutil.cpu_percent()
        ram = self.process.memory_info().rss / 1024 / 1024
        latency = round(self.bot.latency * 1000)

        members = sum(g.member_count for g in self.bot.guilds)

        embed = discord.Embed(
            title="🍃 Bot Status",
            color=discord.Color.blue()
        )

        embed.set_thumbnail(url=self.bot.user.display_avatar.url)

        embed.add_field(
            name="🖱️ CPU",
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
            name="🌍 Servers",
            value=len(self.bot.guilds),
            inline=True
        )

        embed.add_field(
            name="👤 Members",
            value=members,
            inline=True
        )

        embed.set_footer(text=f"Bot: {self.bot.user}")

        await interaction.response.send_message(embed=embed)


async def setup(bot):
    await bot.add_cog(BotSpeed(bot))