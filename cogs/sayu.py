import discord
from discord.ext import commands
from discord import app_commands
from discord.ui import View, Button, Modal, TextInput
from PIL import Image, ImageDraw, ImageFont
import random
import string
import io
import json
import os

CONFIG_FILE = "cogs/config.json"

captcha_cache = {}
verified_users = set()


def load_config():
    if not os.path.exists(CONFIG_FILE):
        return {}

    with open(CONFIG_FILE, "r") as f:
        return json.load(f)


def save_config(data):
    with open(CONFIG_FILE, "w") as f:
        json.dump(data, f, indent=4)


config = load_config()


def generate_text():
    length = random.randint(5, 6)
    chars = string.ascii_uppercase + string.digits
    return "".join(random.choice(chars) for _ in range(length))


def generate_image(text):

    width, height = 420, 170

    image = Image.new("RGB", (width, height), (255, 255, 255))
    draw = ImageDraw.Draw(image)

    try:
        font = ImageFont.truetype("arial.ttf", 80)
    except:
        font = ImageFont.load_default()

    spacing = width // (len(text) + 1)

    for i, char in enumerate(text):

        x = spacing * (i + 1)
        y = random.randint(65, 85)

        draw.text(
            (x, y),
            char,
            font=font,
            fill=(0, 0, 0),
            anchor="mm"
        )

    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    buffer.seek(0)

    return buffer


# ======================
# ADMIN REVIEW
# ======================

class AdminReview(View):

    def __init__(self, user_id, role_id, guild_id, guild_data):

        super().__init__(timeout=None)

        self.user_id = user_id
        self.role_id = role_id
        self.guild_id = guild_id
        self.guild_data = guild_data

    @discord.ui.button(label="ยินดีต้อนรับ", style=discord.ButtonStyle.green)
    async def approve(self, interaction: discord.Interaction, button: Button):

        await interaction.response.defer()

        if not interaction.user.guild_permissions.administrator:
            await interaction.followup.send("แอดมินเท่านั้น", ephemeral=True)
            return

        guild = interaction.guild

        member = guild.get_member(self.user_id)
        role = guild.get_role(self.role_id)

        if member is None or role is None:

            await interaction.followup.send("❌ หา user หรือ role ไม่เจอ", ephemeral=True)
            return

        await member.add_roles(role)

        embed = discord.Embed(
            title="✅ อนุมัติแล้ว",
            description=f"{member.mention} ได้รับ {role.mention}",
            color=discord.Color.green()
        )

        embed.set_thumbnail(url=member.display_avatar.url)

        if self.guild_data["gif_success"]:
            embed.set_image(url=self.guild_data["gif_success"])

        await interaction.message.edit(embed=embed, view=None)

    @discord.ui.button(label="ไม่อนุญาต", style=discord.ButtonStyle.red)
    async def deny(self, interaction: discord.Interaction, button: Button):

        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("แอดมินเท่านั้น", ephemeral=True)
            return

        guild = interaction.guild
        member = guild.get_member(self.user_id)

        embed = discord.Embed(
            title="❌ ปฏิเสธ",
            description=f"{member.mention} ถูกปฏิเสธ",
            color=discord.Color.red()
        )

        await interaction.response.edit_message(embed=embed, view=None)


# ======================
# CAPTCHA MODAL
# ======================

class CaptchaModal(Modal):

    def __init__(self, guild_id):

        super().__init__(title="กรอกรหัสยืนยัน")

        self.guild_id = guild_id

        self.answer = TextInput(
            label="พิมพ์รหัสจากภาพ",
            max_length=6
        )

        self.add_item(self.answer)

    async def on_submit(self, interaction: discord.Interaction):

        user_id = interaction.user.id

        if user_id in verified_users:
            await interaction.response.send_message("คุณยืนยันแล้ว", ephemeral=True)
            return

        correct_code = captcha_cache.get(user_id)

        if self.answer.value.upper() != correct_code:
            await interaction.response.send_message("❌ รหัสไม่ถูกต้อง", ephemeral=True)
            return

        guild_data = config[str(self.guild_id)]

        role = interaction.guild.get_role(guild_data["role"])

        if guild_data["mode"] == "auto":

            await interaction.user.add_roles(role)

            verified_users.add(user_id)

            await interaction.response.send_message(
                f"✅ คุณได้รับ {role.mention}",
                ephemeral=True
            )

        else:

            channel = interaction.guild.get_channel(
                guild_data["admin_channel"]
            )

            embed = discord.Embed(
                title="📨 คำขอยืนยันตัวตน",
                description=f"{interaction.user.mention}\nสถานะ: รอแอดมินตรวจสอบ",
                color=discord.Color.orange()
            )

            embed.set_thumbnail(url=interaction.user.display_avatar.url)

            if guild_data["gif_pending"]:
                embed.set_image(url=guild_data["gif_pending"])

            await channel.send(
                embed=embed,
                view=AdminReview(
                    interaction.user.id,
                    role.id,
                    interaction.guild.id,
                    guild_data
                )
            )

            verified_users.add(user_id)

            await interaction.response.send_message(
                "📩 ส่งคำขอไปให้แอดมินแล้ว",
                ephemeral=True
            )


# ======================
# VERIFY VIEW
# ======================

class VerifyView(View):

    def __init__(self, guild_id):

        super().__init__(timeout=None)

        self.guild_id = guild_id

    @discord.ui.button(label="สุ่มรหัส", style=discord.ButtonStyle.blurple)
    async def generate(self, interaction: discord.Interaction, button: Button):

        text = generate_text()

        captcha_cache[interaction.user.id] = text

        image_buffer = generate_image(text)

        file = discord.File(image_buffer, filename="captcha.png")

        embed = discord.Embed(
            title="🔐 Verify System",
            description="กรอกรหัสจากภาพ",
            color=discord.Color.red()
        )

        embed.set_image(url="attachment://captcha.png")

        await interaction.response.send_message(
            embed=embed,
            file=file,
            ephemeral=True
        )

    @discord.ui.button(label="กรอกรหัส", style=discord.ButtonStyle.green)
    async def input_code(self, interaction: discord.Interaction, button: Button):

        await interaction.response.send_modal(
            CaptchaModal(interaction.guild.id)
        )


# ======================
# COMMAND
# ======================

class Safety(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="safety", description="สร้างระบบ verify")
    @app_commands.checks.has_permissions(administrator=True)

    async def safety(
        self,
        interaction: discord.Interaction,
        role: discord.Role,
        verify_channel: discord.TextChannel,
        admin_channel: discord.TextChannel,
        mode: str
    ):

        config[str(interaction.guild.id)] = {

            "role": role.id,
            "verify_channel": verify_channel.id,
            "admin_channel": admin_channel.id,
            "mode": mode,
            "gif_verify": "",
            "gif_pending": "",
            "gif_success": ""

        }

        save_config(config)

        embed = discord.Embed(
            title="🔐 Verify System",
            description="กดสุ่มรหัสเพื่อยืนยันตัวตน",
            color=discord.Color.green()
        )

        await verify_channel.send(
            embed=embed,
            view=VerifyView(interaction.guild.id)
        )

        await interaction.response.send_message(
            "🍃 สร้างระบบ verify แล้ว",
            ephemeral=True
        )


async def setup(bot):
    await bot.add_cog(Safety(bot))