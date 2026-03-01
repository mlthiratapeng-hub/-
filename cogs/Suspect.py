import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import View, Button, Modal, TextInput
from PIL import Image, ImageDraw, ImageFont
import random
import string
import io

GUILD_REQUIRED_ID = 1476624073990738022  # ต้องอยู่ดิสนี้ก่อนถึงใช้ได้
CAPTCHA_LENGTH = 6

def generate_captcha_text(length=CAPTCHA_LENGTH):
    chars = string.ascii_uppercase + string.digits
    return ''.join(random.choice(chars) for _ in range(length))

def generate_captcha_image(text):
    width = 300
    height = 100
    image = Image.new("RGB", (width, height), (255, 255, 255))
    draw = ImageDraw.Draw(image)

    try:
        font = ImageFont.truetype("arial.ttf", 50)
    except:
        font = ImageFont.load_default()

    # วาดตัวอักษรแบบสุ่มสีและตำแหน่ง
    for i, char in enumerate(text):
        x = 20 + i * 40 + random.randint(-5, 5)
        y = random.randint(10, 30)
        color = (
            random.randint(0, 150),
            random.randint(0, 150),
            random.randint(0, 150)
        )
        draw.text((x, y), char, font=font, fill=color)

    # เส้นกันบอท
    for _ in range(6):
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

    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    buffer.seek(0)
    return buffer

class CaptchaModal(Modal):
    def __init__(self, correct_text):
        super().__init__(title="Verify - Report For Duty")
        self.correct_text = correct_text

        self.answer = TextInput(
            label="พิมพ์ตัวอักษรจากภาพ",
            placeholder="เช่น A9X2PZ",
            max_length=CAPTCHA_LENGTH
        )

        self.add_item(self.answer)

    async def on_submit(self, interaction: discord.Interaction):
        if self.answer.value.upper() == self.correct_text:
            await interaction.response.send_message(
                "📁 ยืนยันตัวตนสำเร็จ",
                ephemeral=True
            )
        else:
            await interaction.response.send_message(
                "🥩 ตัวอักษรไม่ถูกต้อง",
                ephemeral=True
            )

class CaptchaButton(View):
    def __init__(self):
        super().__init__(timeout=300)

    @discord.ui.button(label="Verify Now", style=discord.ButtonStyle.green)
    async def verify(self, interaction: discord.Interaction, button: Button):

        # ตรวจว่าต้องเป็น admin
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message(
                "💢 คำสั่งนี้สำหรับแอดมินเท่านั้น",
                ephemeral=True
            )
            return

        # ตรวจว่าต้องอยู่กิลด์ที่กำหนดก่อน
        required_guild = interaction.client.get_guild(GUILD_REQUIRED_ID)
        if not required_guild or not required_guild.get_member(interaction.user.id):
            await interaction.response.send_message(
                "🌶️ คุณต้องอยู่ในดิสที่กำหนดก่อนถึงใช้ระบบนี้ได้",
                ephemeral=True
            )
            return

        captcha_text = generate_captcha_text()
        image_buffer = generate_captcha_image(captcha_text)

        file = discord.File(image_buffer, filename="captcha.png")

        embed = discord.Embed(
            title="🔐 Report For Duty Verification",
            description="กรุณาพิมพ์ตัวอักษรและตัวเลขจากภาพ",
            color=discord.Color.blue()
        )
        embed.set_image(url="attachment://captcha.png")

        await interaction.response.send_message(
            embed=embed,
            file=file,
            view=CaptchaModal(captcha_text),
            ephemeral=True
        )

class ReportForDuty(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="reportforduty", description="ระบบยืนยันตัวตนสำหรับแอดมิน")
    async def reportforduty(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="🛡 Report For Duty",
            description="กดปุ่มด้านล่างเพื่อยืนยันตัวตน",
            color=discord.Color.green()
        )

        await interaction.response.send_message(
            embed=embed,
            view=CaptchaButton()
        )

async def setup(bot):
    await bot.add_cog(ReportForDuty(bot))