import discord
from discord.ext import commands
from discord import app_commands
import json
import os

DATA_FILE = "cogs/data/welcome.json"


def load_data():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)


data = load_data()


class WelcomeMenu(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot

    @discord.ui.button(label="⚙️ ตั้งค่าข้อความ", style=discord.ButtonStyle.gray)
    async def set_message(self, interaction: discord.Interaction, button: discord.ui.Button):

        await interaction.response.send_modal(WelcomeModal())

    @discord.ui.button(label="📢 เลือกห้อง", style=discord.ButtonStyle.gray)
    async def set_channel(self, interaction: discord.Interaction, button: discord.ui.Button):

        view = ChannelSelectView()
        await interaction.response.send_message(
            "เลือกห้อง Welcome",
            view=view,
            ephemeral=True
        )

    @discord.ui.button(label="🧪 เทสระบบ", style=discord.ButtonStyle.green)
    async def test(self, interaction: discord.Interaction, button: discord.ui.Button):

        guild_id = str(interaction.guild.id)

        if guild_id not in data:
            await interaction.response.send_message("🍎 ยังไม่ได้ตั้งค่า", ephemeral=True)
            return

        channel = interaction.guild.get_channel(data[guild_id]["channel"])

        fake = interaction.user

        msg = data[guild_id]["message"]

        msg = msg.replace("{user}", fake.mention)
        msg = msg.replace("{server}", interaction.guild.name)
        msg = msg.replace("{membercount}", str(interaction.guild.member_count))

        embed = discord.Embed(
            title="🍇 Welcome",
            description=msg,
            color=discord.Color.green()
        )

        embed.set_thumbnail(url=fake.display_avatar.url)

        await channel.send(embed=embed)

        await interaction.response.send_message("🍲 เทสสำเร็จ", ephemeral=True)


class WelcomeModal(discord.ui.Modal, title="ตั้งค่าข้อความ Welcome"):

    message = discord.ui.TextInput(
        label="ข้อความ",
        placeholder="ยินดีต้อนรับ {user}",
        style=discord.TextStyle.paragraph,
        max_length=500
    )

    async def on_submit(self, interaction: discord.Interaction):

        guild_id = str(interaction.guild.id)

        if guild_id not in data:
            data[guild_id] = {}

        data[guild_id]["message"] = self.message.value

        save_data(data)

        await interaction.response.send_message(
            "📁 บันทึกข้อความแล้ว",
            ephemeral=True
        )


class ChannelSelectView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=60)
        self.add_item(ChannelDropdown())


class ChannelDropdown(discord.ui.ChannelSelect):

    def __init__(self):
        super().__init__(
            placeholder="เลือกห้อง",
            channel_types=[discord.ChannelType.text]
        )

    async def callback(self, interaction: discord.Interaction):

        guild_id = str(interaction.guild.id)

        if guild_id not in data:
            data[guild_id] = {}

        data[guild_id]["channel"] = self.values[0].id

        save_data(data)

        await interaction.response.send_message(
            f"🍃 ตั้งค่าห้องแล้ว: {self.values[0].mention}",
            ephemeral=True
        )


class Welcome(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="welcome",
        description="ตั้งค่าระบบต้อนรับสมาชิก"
    )
    async def welcome(self, interaction: discord.Interaction):

        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message(
                "🌶️ เฉพาะแอดมินเท่านั้น",
                ephemeral=True
            )
            return

        embed = discord.Embed(
            title="🍇 Welcome System",
            description="ตั้งค่าระบบต้อนรับสมาชิก",
            color=discord.Color.green()
        )

        embed.add_field(
            name="ตัวแปร",
            value="""
{user} = แท็กสมาชิก
{server} = ชื่อเซิร์ฟ
{membercount} = จำนวนสมาชิก
""",
            inline=False
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

        if "channel" not in data[guild_id] or "message" not in data[guild_id]:
            return

        channel = member.guild.get_channel(data[guild_id]["channel"])

        msg = data[guild_id]["message"]

        msg = msg.replace("{user}", member.mention)
        msg = msg.replace("{server}", member.guild.name)
        msg = msg.replace("{membercount}", str(member.guild.member_count))

        embed = discord.Embed(
            title="🍇 Welcome",
            description=msg,
            color=discord.Color.green()
        )

        embed.set_thumbnail(url=member.display_avatar.url)

        await channel.send(embed=embed)


async def setup(bot):
    await bot.add_cog(Welcome(bot))