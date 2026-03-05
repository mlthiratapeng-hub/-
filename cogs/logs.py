import discord
from discord.ext import commands
from discord import app_commands

class Logs(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.log_channels = {}  # เก็บ log channel ต่อเซิร์ฟเวอร์

    # =========================
    # /logall
    # =========================
    @app_commands.command(name="logall", description="ตั้งค่าห้องสำหรับเก็บ Log")
    async def logall(self, interaction: discord.Interaction, channel: discord.TextChannel):

        if interaction.guild is None:
            return await interaction.response.send_message(
                "💢 ใช้ได้เฉพาะในเซิร์ฟเวอร์",
                ephemeral=True
            )

        if not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message(
                "💢 Admin only",
                ephemeral=True
            )

        self.log_channels[interaction.guild.id] = channel.id

        await interaction.response.send_message(
            f"📁 ตั้งค่าห้อง Log เป็น {channel.mention} แล้ว",
            ephemeral=True
        )

    # =========================
    # ลบข้อความ
    # =========================
    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message):

        if message.guild is None:
            return

        channel_id = self.log_channels.get(message.guild.id)
        if not channel_id:
            return

        log_channel = message.guild.get_channel(channel_id)
        if not log_channel:
            return

        embed = discord.Embed(
            title="🗑 ลบข้อความ",
            color=discord.Color.red()
        )
        embed.add_field(name="🙍ผู้ใช้", value=message.author.mention, inline=False)
        embed.add_field(name="📁ช่อง", value=message.channel.mention, inline=False)
        embed.add_field(name="🗯️ข้อความ", value=message.content or "💢ไม่มีข้อความ", inline=False)

        await log_channel.send(embed=embed)

    # =========================
    # แก้ไขข้อความ
    # =========================
    @commands.Cog.listener()
    async def on_message_edit(self, before: discord.Message, after: discord.Message):

        if before.guild is None:
            return

        if before.content == after.content:
            return

        channel_id = self.log_channels.get(before.guild.id)
        if not channel_id:
            return

        log_channel = before.guild.get_channel(channel_id)
        if not log_channel:
            return

        embed = discord.Embed(
            title="✏ แก้ไขข้อความ",
            color=discord.Color.orange()
        )
        embed.add_field(name="📁ผู้ใช้", value=before.author.mention, inline=False)
        embed.add_field(name="💾ก่อนแก้", value=before.content or "ไม่มีข้อความ", inline=False)
        embed.add_field(name="📁หลังแก้", value=after.content or "ไม่มีข้อความ", inline=False)

        await log_channel.send(embed=embed)

    # =========================
    # คนเข้า
    # =========================
    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):

        channel_id = self.log_channels.get(member.guild.id)
        if not channel_id:
            return

        log_channel = member.guild.get_channel(channel_id)
        if not log_channel:
            return

        await log_channel.send(f"🍲 {member.mention} เข้าร่วมเซิร์ฟเวอร์")

    # =========================
    # คนออก
    # =========================
    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):

        channel_id = self.log_channels.get(member.guild.id)
        if not channel_id:
            return

        log_channel = member.guild.get_channel(channel_id)
        if not log_channel:
            return

        await log_channel.send(f"🍄 {member.name} ออกจากเซิร์ฟเวอร์")


async def setup(bot: commands.Bot):
    await bot.add_cog(Logs(bot))