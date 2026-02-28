import discord
from discord.ext import commands
from discord import app_commands

class Whitelist(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.whitelist = set()  # เก็บ user id ที่ whitelist

    # =========================
    # /whitelist add
    # =========================
    @app_commands.command(name="whitelist_add", description="เพิ่มผู้ใช้เข้า whitelist")
    async def whitelist_add(self, interaction: discord.Interaction, user: discord.Member):

        if not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message(
                "💢 Admin only",
                ephemeral=True
            )

        self.whitelist.add(user.id)

        await interaction.response.send_message(
            f"🫛 เพิ่ม {user.mention} เข้า Whitelist แล้ว",
            ephemeral=True
        )

    # =========================
    # /whitelist remove
    # =========================
    @app_commands.command(name="whitelist_remove", description="ลบผู้ใช้ออกจาก whitelist")
    async def whitelist_remove(self, interaction: discord.Interaction, user: discord.Member):

        if not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message(
                "💢 Admin only",
                ephemeral=True
            )

        self.whitelist.discard(user.id)

        await interaction.response.send_message(
            f"🗑 ลบ {user.mention} ออกจาก Whitelist แล้ว",
            ephemeral=True
        )

    # =========================
    # /whitelist list
    # =========================
    @app_commands.command(name="whitelist_list", description="ดูรายชื่อ whitelist")
    async def whitelist_list(self, interaction: discord.Interaction):

        if not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message(
                "💢 Admin only",
                ephemeral=True
            )

        if not self.whitelist:
            return await interaction.response.send_message(
                "📄 ยังไม่มีใครอยู่ใน whitelist",
                ephemeral=True
            )

        users = "\n".join([f"<@{uid}>" for uid in self.whitelist])

        embed = discord.Embed(
            title="📄 Whitelist",
            description=users,
            color=discord.Color.green()
        )

        await interaction.response.send_message(embed=embed, ephemeral=True)


    # =========================
    # ให้ไฟล์อื่นเรียกใช้
    # =========================
    def is_whitelisted(self, user_id: int):
        return user_id in self.whitelist


async def setup(bot: commands.Bot):
    await bot.add_cog(Whitelist(bot))