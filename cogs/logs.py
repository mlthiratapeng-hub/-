import discord
from discord.ext import commands
from discord import app_commands
import sqlite3

DB = "data.db"


def get_log_channel(guild_id):
    conn = sqlite3.connect(DB)
    c = conn.cursor()

    c.execute("SELECT channel_id FROM logs WHERE guild_id=?", (guild_id,))
    result = c.fetchone()

    conn.close()

    if result:
        return result[0]
    return None


def set_log_channel(guild_id, channel_id):
    conn = sqlite3.connect(DB)
    c = conn.cursor()

    c.execute(
        "INSERT OR REPLACE INTO logs (guild_id, channel_id) VALUES (?,?)",
        (guild_id, channel_id)
    )

    conn.commit()
    conn.close()


class Logs(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # =================
    # /logall
    # =================

    @app_commands.command(name="logall", description="ตั้งค่าห้อง Log")
    async def logall(self, interaction: discord.Interaction, channel: discord.TextChannel):

        if not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message(
                "💢 Admin only",
                ephemeral=True
            )

        set_log_channel(interaction.guild.id, channel.id)

        await interaction.response.send_message(
            f"📁 ตั้งค่าห้อง Log เป็น {channel.mention} แล้ว",
            ephemeral=True
        )

    # =================
    # ลบข้อความ
    # =================

    @commands.Cog.listener()
    async def on_message_delete(self, message):

        if not message.guild:
            return

        channel_id = get_log_channel(message.guild.id)

        if not channel_id:
            return

        log_channel = message.guild.get_channel(channel_id)

        if not log_channel:
            return

        embed = discord.Embed(
            title="🗑 ลบข้อความ",
            color=discord.Color.red()
        )

        embed.add_field(name="👤 ผู้ใช้", value=message.author.mention, inline=False)
        embed.add_field(name="🕸️ ห้อง", value=message.channel.mention, inline=False)
        embed.add_field(name="📁 ข้อความ", value=message.content or "🌮 ไม่มีข้อความ", inline=False)

        await log_channel.send(embed=embed)

    # =================
    # คนเข้า
    # =================

    @commands.Cog.listener()
    async def on_member_join(self, member):

        channel_id = get_log_channel(member.guild.id)

        if not channel_id:
            return

        log_channel = member.guild.get_channel(channel_id)

        if log_channel:
            await log_channel.send(f"🍇 {member.mention} เข้าร่วมเซิร์ฟเวอร์")

    # =================
    # คนออก
    # =================

    @commands.Cog.listener()
    async def on_member_remove(self, member):

        channel_id = get_log_channel(member.guild.id)

        if not channel_id:
            return

        log_channel = member.guild.get_channel(channel_id)

        if log_channel:
            await log_channel.send(f"📤 {member.name} ออกจากเซิร์ฟเวอร์")


async def setup(bot):
    await bot.add_cog(Logs(bot))