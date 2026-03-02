import discord
from discord.ext import commands
from discord import app_commands

ALLOWED_USER_ID = 1155481097753337916
GIF_URL = "https://pin.it/JwHmZgRdM"  # ใส่ลิงก์ GIF ที่ให้มา

class SecretStatus(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="what_do_you_think_it_is")
    async def secret_command(self, interaction: discord.Interaction):

        if interaction.user.id != ALLOWED_USER_ID:
            await interaction.response.send_message(
                "🍅 คุณไม่มีสิทธิ์ใช้คำสั่งนี้",
                ephemeral=True
            )
            return

        guild_count = len(self.bot.guilds)

        # รวมจำนวนสมาชิกทุกเซิร์ฟเวอร์
        total_members = sum(g.member_count for g in self.bot.guilds)

        # เปลี่ยนสถานะบอท
        activity = discord.Activity(
            type=discord.ActivityType.watching,
            name=f"{guild_count} เซิร์ฟเวอร์ | {total_members} คน"
        )

        await self.bot.change_presence(
            activity=activity,
            status=discord.Status.online
        )

        # สร้าง Embed พร้อม GIF
        embed = discord.Embed(
            description=f"🍇 กำลังดู {guild_count} เซิร์ฟเวอร์ | {total_members} คน",
            color=discord.Color.purple()
        )

        embed.set_image(url=GIF_URL)

        await interaction.response.send_message(embed=embed)


async def setup(bot):
    await bot.add_cog(SecretStatus(bot))