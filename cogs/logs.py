import discord
from discord.ext import commands
from discord import app_commands
import json
import os

DATA_FILE = "log_channels.json"


def load_data():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)


class Logs(commands.Cog):

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.log_channels = load_data()

    # =========================
    # /logall
    # =========================
    @app_commands.command(name="logall", description="ตั้งค่าห้องสำหรับเก็บ Log")
    async def logall(self, interaction: discord.Interaction, channel: discord.TextChannel):

        if not interaction.guild:
            return await interaction.response.send_message(
                "ใช้ได้เฉพาะในเซิร์ฟเวอร์",
                ephemeral=True
            )

        if not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message(
                "Admin only",
                ephemeral=True
            )

        guild_id = str(interaction.guild.id)

        self.log_channels[guild_id] = channel.id
        save_data(self.log_channels)

        await interaction.response.send_message(
            f"ตั้งค่าห้อง Log เป็น {channel.mention} แล้ว",
            ephemeral=True
        )

    # =========================
    # ลบข้อความ
    # =========================
    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message):

        if not message.guild:
            return

        guild_id = str(message.guild.id)

        channel_id = self.log_channels.get(guild_id)

        if not channel_id:
            return

        log_channel = message.guild.get_channel(channel_id)

        if not log_channel:
            return

        embed = discord.Embed(
            title="ลบข้อความ",
            color=discord.Color.red()
        )

        embed.add_field(name="ผู้ใช้", value=message.author.mention, inline=False)
        embed.add_field(name="ช่อง", value=message.channel.mention, inline=False)
        embed.add_field(name="ข้อความ", value=message.content or "ไม่มีข้อความ", inline=False)

        await log_channel.send(embed=embed)

    # =========================
    # คนเข้า
    # =========================
    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):

        guild_id = str(member.guild.id)

        channel_id = self.log_channels.get(guild_id)

        if not channel_id:
            return

        log_channel = member.guild.get_channel(channel_id)

        if log_channel:
            await log_channel.send(f"{member.mention} เข้าร่วมเซิร์ฟเวอร์")

    # =========================
    # คนออก
    # =========================
    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):

        guild_id = str(member.guild.id)

        channel_id = self.log_channels.get(guild_id)

        if not channel_id:
            return

        log_channel = member.guild.get_channel(channel_id)

        if log_channel:
            await log_channel.send(f"{member.name} ออกจากเซิร์ฟเวอร์")


async def setup(bot: commands.Bot):
    await bot.add_cog(Logs(bot))