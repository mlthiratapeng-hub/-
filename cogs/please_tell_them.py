import discord
from discord.ext import commands
from discord import app_commands


class TellModal(discord.ui.Modal, title="ฝากข้อความ"):

    fake_name = discord.ui.TextInput(
        label="ตัวตนปลอม",
        placeholder="เช่น คนที่ลักหลับเธอ",
        max_length=100
    )

    message = discord.ui.TextInput(
        label="ข้อความ",
        style=discord.TextStyle.paragraph,
        max_length=500
    )

    hint = discord.ui.TextInput(
        label="คำใบ้",
        placeholder="ใบ้",
        max_length=200
    )

    def __init__(self, target):
        super().__init__()
        self.target = target

    async def on_submit(self, interaction: discord.Interaction):

        embed = discord.Embed(
            title="📨 มีคนฝากข้อความมาถึงคุณ",
            color=discord.Color.blurple()
        )

        embed.add_field(
            name="👤 ถึง",
            value=self.target.mention,
            inline=False
        )

        embed.add_field(
            name="🕵️ ตัวตน",
            value=self.fake_name.value,
            inline=False
        )

        embed.add_field(
            name="💬 ข้อความ",
            value=self.message.value,
            inline=False
        )

        embed.add_field(
            name="🔎 คำใบ้",
            value=self.hint.value,
            inline=False
        )

        embed.set_thumbnail(url=self.target.display_avatar.url)

        await interaction.response.send_message(
            content=self.target.mention,
            embed=embed
        )


class PleaseTellThem(commands.Cog):

    def __init__(self, bot):
        self.bot = bot


    @app_commands.command(name="please_tell_them", description="ฝากบอกข้อความแบบไม่เปิดเผยตัว")
    async def please_tell_them(self, interaction: discord.Interaction, target: discord.Member):

        modal = TellModal(target)
        await interaction.response.send_modal(modal)


async def setup(bot):
    await bot.add_cog(PleaseTellThem(bot))