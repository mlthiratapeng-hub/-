import discord
from discord.ext import commands
from discord import app_commands
import json
import os

DATA_FILE = "goodbye_data.json"


def load_data():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)


data = load_data()


class GoodbyeMain(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot

    @discord.ui.button(label="⚙️ ตั้งค่าข้อความ", style=discord.ButtonStyle.gray)
    async def set_message(self, interaction: discord.Interaction, button: discord.ui.Button):

        modal = GoodbyeModal(self.bot)
        await interaction.response.send_modal(modal)

    @discord.ui.button(label="📢 เลือกห้อง", style=discord.ButtonStyle.gray)
    async def set_channel(self, interaction: discord.Interaction, button: discord.ui.Button):

        view = ChannelSelect(self.bot)
        await interaction.response.send_message(
            "เลือกห้องสำหรับ Goodbye",
            view=view,
            ephemeral=True
        )

    @discord.ui.button(label="🧪 เทสระบบ", style=discord.ButtonStyle.green)
    async def test(self, interaction: discord.Interaction, button: discord.ui.Button):

        guild_id = str(interaction.guild.id)

        if guild_id not in data:
            await interaction.response.send_message("🍒 ยังไม่ได้ตั้งค่า", ephemeral=True)
            return

        if "channel" not in data[guild_id] or "message" not in data[guild_id]:
            await interaction.response.send_message("🦞 ยังตั้งค่าไม่ครบ", ephemeral=True)
            return

        channel = interaction.guild.get_channel(data[guild_id]["channel"])

        fake = interaction.user

        embed = discord.Embed(
            title="👋😍🍃 Goodbye",
            description=data[guild_id]["message"].replace("{user}", fake.mention),
            color=discord.Color.red()
        )

        embed.set_thumbnail(url=fake.display_avatar.url)

        await channel.send(embed=embed)

        await interaction.response.send_message("🍇 เทสสำเร็จ", ephemeral=True)


class GoodbyeModal(discord.ui.Modal, title="ตั้งค่าข้อความ Goodbye"):

    message = discord.ui.TextInput(
        label="ข้อความ Goodbye",
        placeholder="ลาก่อน {user}",
        style=discord.TextStyle.paragraph,
        max_length=500
    )

    def __init__(self, bot):
        super().__init__()
        self.bot = bot

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


class ChannelSelect(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=60)
        self.bot = bot

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
            f"🥝 ตั้งค่าห้องแล้ว: {self.values[0].mention}",
            ephemeral=True
        )


class Goodbye(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="goodbye",
        description="ตั้งค่าระบบ goodbye"
    )
    async def goodbye(self, interaction: discord.Interaction):

        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message(
                "🌶️ เฉพาะแอดมินเท่านั้น",
                ephemeral=True
            )
            return

        embed = discord.Embed(
            title="🍃 Goodbye System",
            description="ตั้งค่าระบบลาออกจากเซิร์ฟเวอร์",
            color=discord.Color.red()
        )

        embed.add_field(
            name="ตัวแปรที่ใช้ได้",
            value="""
{user} = ชื่อคนออก
{server} = ชื่อเซิร์ฟ
""",
            inline=False
        )

        await interaction.response.send_message(
            embed=embed,
            view=GoodbyeMain(self.bot),
            ephemeral=True
        )

    @commands.Cog.listener()
    async def on_member_remove(self, member):

        guild_id = str(member.guild.id)

        if guild_id not in data:
            return

        if "channel" not in data[guild_id] or "message" not in data[guild_id]:
            return

        channel = member.guild.get_channel(data[guild_id]["channel"])

        if channel is None:
            return

        message = data[guild_id]["message"]

        message = message.replace("{user}", member.mention)
        message = message.replace("{server}", member.guild.name)

        embed = discord.Embed(
            title="🍃 Goodbye",
            description=message,
            color=discord.Color.red()
        )

        embed.set_thumbnail(url=member.display_avatar.url)

        await channel.send(embed=embed)


async def setup(bot):
    await bot.add_cog(Goodbye(bot))