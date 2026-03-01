import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import View, Button, Modal, TextInput
from PIL import Image, ImageDraw, ImageFont
import random
import string
import io

GUILD_REQUIRED_ID = 1476624073990738022
VERIFIED_ROLE_ID = 1476897558679912541  # 🔥 เปลี่ยนเป็น role id จริง
CAPTCHA_LENGTH = 6


# ================= CAPTCHA =================

def generate_captcha_text(length=CAPTCHA_LENGTH):
    chars = string.ascii_uppercase + string.digits
    return ''.join(random.choice(chars) for _ in range(length))


def generate_captcha_image(text):
    width = 320
    height = 120
    image = Image.new("RGB", (width, height), (255, 255, 255))
    draw = ImageDraw.Draw(image)

    try:
        font = ImageFont.truetype("arial.ttf", 55)
    except:
        font = ImageFont.load_default()

    # ตัวอักษรมั่วตำแหน่ง + สี
    for i, char in enumerate(text):
        x = 30 + i * 45 + random.randint(-5, 5)
        y = 30 + random.randint(-10, 10)
        color = (
            random.randint(0, 150),
            random.randint(0, 150),
            random.randint(0, 150)
        )
        draw.text((x, y), char, font=font, fill=color)

    # เส้นรบกวน
    for _ in range(8):
        draw.line(
            (
                random.randint(0, width),
                random.randint(0, height),
                random.randint(0, width),
                random.randint(0, height)
            ),
            fill=(
                random.randint(0, 255),
                random.randint(0, 255),
                random.randint(0, 255)
            ),
            width=2
        )

    # จุด noise
    for _ in range(300):
        draw.point(
            (random.randint(0, width), random.randint(0, height)),
            fill=(
                random.randint(0, 255),
                random.randint(0, 255),
                random.randint(0, 255)
            )
        )

    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    buffer.seek(0)
    return buffer


# ================= MODAL =================

class CaptchaModal(Modal):
    def __init__(self, correct_text):
        super().__init__(title="Report For Duty Verification")
        self.correct_text = correct_text

        self.answer = TextInput(
            label="พิมพ์ตัวอักษรและตัวเลขตามภาพ",
            placeholder="Enter captcha here",
            max_length=CAPTCHA_LENGTH,
            required=True
        )

        self.add_item(self.answer)

    async def on_submit(self, interaction: discord.Interaction):

        embed = discord.Embed(color=discord.Color.red())

        if self.answer.value.upper() == self.correct_text:

            role = interaction.guild.get_role(VERIFIED_ROLE_ID)

            if role:
                await interaction.user.add_roles(role)

            embed.title = "🥬 Verification Successful"
            embed.description = f"คุณได้รับยศเรียบร้อยแล้ว\nRole: {role.mention if role else 'ไม่พบ role'}"
            embed.color = discord.Color.green()

        else:
            embed.title = "❌ Verification Failed"
            embed.description = "ตัวอักษรไม่ถูกต้อง กรุณาลองใหม่"
            embed.color = discord.Color.red()

        await interaction.response.send_message(embed=embed, ephemeral=True)


# ================= VIEW =================

class VerifyView(View):
    def __init__(self):
        super().__init__(timeout=300)

    @discord.ui.button(label="Report For Duty", style=discord.ButtonStyle.green)
    async def verify(self, interaction: discord.Interaction, button: Button):

        # เช็ค admin
        if not interaction.user.guild_permissions.administrator:
            embed = discord.Embed(
                title="❌ Permission Denied",
                description="คำสั่งนี้ใช้ได้เฉพาะแอดมิน",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        # เช็คต้องอยู่ดิสหลักก่อน
        required_guild = interaction.client.get_guild(GUILD_REQUIRED_ID)

        if not required_guild or not required_guild.get_member(interaction.user.id):
            embed = discord.Embed(
                title="❌ Access Denied",
                description="คุณต้องอยู่ในดิสที่กำหนดก่อนถึงใช้ระบบนี้ได้",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        captcha_text = generate_captcha_text()
        image_buffer = generate_captcha_image(captcha_text)

        file = discord.File(image_buffer, filename="captcha.png")

        embed = discord.Embed(
            title="🔐 Identity Verification Required",
            description="กรุณาพิมพ์ตัวอักษรและตัวเลขจากภาพด้านล่าง",
            color=discord.Color.blurple()
        )

        embed.set_image(url="attachment://captcha.png")

        await interaction.response.send_message(
            embed=embed,
            file=file,
            view=CaptchaInputView(captcha_text),
            ephemeral=True
        )


class CaptchaInputView(View):
    def __init__(self, captcha_text):
        super().__init__(timeout=120)
        self.captcha_text = captcha_text

    @discord.ui.button(label="กรอกคำตอบ", style=discord.ButtonStyle.primary)
    async def input_button(self, interaction: discord.Interaction, button: Button):
        await interaction.response.send_modal(
            CaptchaModal(self.captcha_text)
        )


# ================= COG =================

class ReportForDuty(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="advanced_protection", description="ระบบยืนยันตัวตน slfe-bot")
    async def reportforduty(self, interaction: discord.Interaction):

        embed = discord.Embed(
            title="🛡 Report For Duty System",
            description="กดปุ่มด้านล่างเพื่อทำการยืนยันตัวตน",
            color=discord.Color.blue()
        )

        await interaction.response.send_message(
            embed=embed,
            view=VerifyView()
        )


async def setup(bot):
    await bot.add_cog(ReportForDuty(bot))