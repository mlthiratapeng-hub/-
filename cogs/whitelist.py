import discord
from discord.ext import commands
from discord import app_commands


class Whitelist(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        # เก็บ whitelist แยกตาม guild
        # รูปแบบ: { guild_id: set(user_id) }
        self.whitelist = {}

    # =========================
    # เช็คสิทธิ์แอดมิน
    # =========================
    def is_admin(self, interaction: discord.Interaction):
        return interaction.user.guild_permissions.administrator

    # =========================
    # /whitelist_add
    # =========================
    @app_commands.command(name="whitelist_add", description="เพิ่มผู้ใช้เข้า whitelist")
    async def whitelist_add(self, interaction: discord.Interaction, user: discord.Member):

        if not self.is_admin(interaction):
            return await interaction.response.send_message(
                "💢 คำสั่งนี้ใช้ได้เฉพาะแอดมินของเซิร์ฟเวอร์นี้",
                ephemeral=True
            )

        guild_id = interaction.guild.id

        if guild_id not in self.whitelist:
            self.whitelist[guild_id] = set()

        self.whitelist[guild_id].add(user.id)

        embed = discord.Embed(
            title="🫛 เพิ่มเข้า Whitelist",
            description=f"{user.mention} จะไม่ถูกตรวจสอบโดยระบบของบอท",
            color=discord.Color.green()
        )

        await interaction.response.send_message(embed=embed, ephemeral=True)

    # =========================
    # /whitelist_remove
    # =========================
    @app_commands.command(name="whitelist_remove", description="ลบผู้ใช้ออกจาก whitelist")
    async def whitelist_remove(self, interaction: discord.Interaction, user: discord.Member):

        if not self.is_admin(interaction):
            return await interaction.response.send_message(
                "💢 คำสั่งนี้ใช้ได้เฉพาะแอดมินของเซิร์ฟเวอร์นี้",
                ephemeral=True
            )

        guild_id = interaction.guild.id

        if guild_id in self.whitelist:
            self.whitelist[guild_id].discard(user.id)

        embed = discord.Embed(
            title="🗑 ลบออกจาก Whitelist",
            description=f"{user.mention} จะถูกตรวจสอบตามปกติแล้ว",
            color=discord.Color.red()
        )

        await interaction.response.send_message(embed=embed, ephemeral=True)

    # =========================
    # /whitelist_list
    # =========================
    @app_commands.command(name="whitelist_list", description="ดูรายชื่อ whitelist")
    async def whitelist_list(self, interaction: discord.Interaction):

        if not self.is_admin(interaction):
            return await interaction.response.send_message(
                "💢 คำสั่งนี้ใช้ได้เฉพาะแอดมินของเซิร์ฟเวอร์นี้",
                ephemeral=True
            )

        guild_id = interaction.guild.id

        if guild_id not in self.whitelist or not self.whitelist[guild_id]:
            return await interaction.response.send_message(
                "📄 ยังไม่มีใครอยู่ใน whitelist",
                ephemeral=True
            )

        users = "\n".join([f"<@{uid}>" for uid in self.whitelist[guild_id]])

        embed = discord.Embed(
            title="📄 รายชื่อ Whitelist",
            description=users,
            color=discord.Color.blurple()
        )

        await interaction.response.send_message(embed=embed, ephemeral=True)

    # =========================
    # ให้ไฟล์อื่นเรียกใช้
    # =========================
    def is_whitelisted(self, guild_id: int, user_id: int):
        return (
            guild_id in self.whitelist and
            user_id in self.whitelist[guild_id]
        )


async def setup(bot: commands.Bot):
    await bot.add_cog(Whitelist(bot))