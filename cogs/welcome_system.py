import discord
from discord.ext import commands
from discord import app_commands
import json
import os

DATA_FILE = "data/welcome.json"

def load_data():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

data = load_data()


class WelcomeMenu(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot

    @discord.ui.button(label="⚙️ เซ็ตข้อความ", style=discord.ButtonStyle.gray)
    async def set_message(self, interaction: discord.Interaction, button: discord.ui.Button):

        modal = WelcomeModal(self.bot)
        await interaction.response.send_modal(modal)

    @discord.ui.button(label="🧪 เทสระบบ", style=discord.ButtonStyle.green)
    async def test_system(self, interaction: discord.Interaction, button: discord.ui.Button):

        guild_id = str(interaction.guild.id)

        if guild_id not in data:
            await interaction.response.send_message("🍅 ยังไม่ได้ตั้งค่า", ephemeral=True)
            return

        channel = interaction.guild.get_channel(data[guild_id]["channel"])

        fake_user = interaction.user

        embed = discord.Embed(
            title="🍃 Welcome!",
            description=data[guild_id]["message"].replace("{user}", fake_user.mention),
            color=discord.Color.green()
        )

        embed.set_thumbnail(url=fake_user.display_avatar.url)

        await channel.send(embed=embed)

        await interaction.response.send_message("🥡 ทดสอบแล้ว", ephemeral=True)


class WelcomeModal(discord.ui.Modal, title="ตั้งค่าข้อความ Welcome"):

    message = discord.ui.TextInput(
        label="ข้อความ",
        placeholder="เช่น ยินดีต้อนรับ {user}",
        style=discord.TextStyle.paragraph
    )

    def __init__(self, bot):
        super().__init__()
        self.bot = bot

    async def on_submit(self, interaction: discord.Interaction):

        guild_id = str(interaction.guild.id)

        data[guild_id] = {
            "message": self.message.value,
            "channel": interaction.channel.id
        }

        save_data(data)

        await interaction.response.send_message("📁 บันทึกแล้ว", ephemeral=True)


class Welcome(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="welcome",
        description="ตั้งค่าระบบ welcome"
    )
    async def welcome(self, interaction: discord.Interaction):

        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message(
                "🌶️ คำสั่งนี้สำหรับแอดมินเท่านั้นค่ะ",
                ephemeral=True
            )
            return

        embed = discord.Embed(
            title="⚙️ Setting Welcome",
            description="ตั้งค่าระบบต้อนรับสมาชิก",
            color=discord.Color.blue()
        )

        await interaction.response.send_message(
            embed=embed,
            view=WelcomeMenu(self.bot),
            ephemeral=True
        )

    @commands.Cog.listener()
    async def on_member_join(self, member):

        guild_id = str(member.guild.id)

        if guild_id not in data:
            return

        channel = member.guild.get_channel(data[guild_id]["channel"])

        embed = discord.Embed(
            title="🍃 Welcome!",
            description=data[guild_id]["message"].replace("{user}", member.mention),
            color=discord.Color.green()
        )

        embed.set_thumbnail(url=member.display_avatar.url)

        await channel.send(embed=embed)


async def setup(bot):
    await bot.add_cog(Welcome(bot))