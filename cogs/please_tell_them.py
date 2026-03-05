import discord
from discord.ext import commands
from discord import app_commands


class PleaseTellThem(commands.Cog):

    def __init__(self, bot):
        self.bot = bot


    @app_commands.command(
        name="please_tell_them",
        description="ฝากบอกข้อความกับใครบางคนโดยใช้ตัวตนปลอม"
    )
    @app_commands.describe(
        target="คนที่ต้องการฝากบอก",
        fake_name="ชื่อตัวตนปลอมของคุณ",
        message="ข้อความที่ต้องการบอก",
        hint="คำใบ้ว่าเป็นใคร"
    )
    async def please_tell_them(
        self,
        interaction: discord.Interaction,
        target: discord.Member,
        fake_name: str,
        message: str,
        hint: str
    ):

        embed = discord.Embed(
            title="📨 มีคนฝากข้อความมาถึงคุณ",
            color=discord.Color.blurple()
        )

        embed.add_field(
            name="👤 ถึง",
            value=target.mention,
            inline=False
        )

        embed.add_field(
            name="🕵️ ตัวตน",
            value=fake_name,
            inline=False
        )

        embed.add_field(
            name="💬 ข้อความ",
            value=message,
            inline=False
        )

        embed.add_field(
            name="🥡 คำใบ้",
            value=hint,
            inline=False
        )

        embed.set_thumbnail(url=target.display_avatar.url)

        embed.set_footer(
            text=f"ส่งผ่าน {interaction.guild.name}",
            icon_url=interaction.guild.icon.url if interaction.guild.icon else None
        )

        await interaction.response.send_message(
            content=target.mention,
            embed=embed
        )


async def setup(bot):
    await bot.add_cog(PleaseTellThem(bot))