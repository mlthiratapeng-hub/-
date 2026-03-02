import discord
from discord.ext import commands
from discord import app_commands


class Delete(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="delete", description="ลบข้อความตามจำนวนที่กำหนด")
    @app_commands.describe(amount="จำนวนข้อความที่ต้องการลบ (สูงสุด 99999)")
    async def delete(self, interaction: discord.Interaction, amount: int):

        # เช็คสิทธิ์
        if not interaction.user.guild_permissions.manage_messages:
            await interaction.response.send_message(
                "🍅 คำสั่งนี้ใช้ได้เฉพาะคนที่มีสิทธิ์จัดการข้อความ",
                ephemeral=True
            )
            return

        if amount <= 0:
            await interaction.response.send_message(
                "🌶️ ต้องใส่จำนวนมากกว่า 0",
                ephemeral=True
            )
            return

        if amount > 99999:
            amount = 100  # Discord limit

        await interaction.response.defer(ephemeral=True)

        deleted = await interaction.channel.purge(limit=amount)

        embed = discord.Embed(
            title="🗑 ลบข้อความสำเร็จ",
            description=f"ลบไปแล้ว {len(deleted)} ข้อความ",
            color=discord.Color.red()
        )

        await interaction.followup.send(embed=embed, ephemeral=True)


async def setup(bot):
    await bot.add_cog(Delete(bot))