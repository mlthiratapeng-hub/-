import discord
from discord.ext import commands
from discord import app_commands
from discord.ui import View, Button, Modal, TextInput
from PIL import Image, ImageDraw, ImageFont
import random
import string
import io

# เก็บ captcha ชั่วคราว {user_id: code}
captcha_cache = {}


# ===== CAPTCHA =====

def generate_text():
    length = random.randint(4, 8)
    chars = string.ascii_uppercase + string.digits
    return "".join(random.choice(chars) for _ in range(length))


def generate_image(text):
    width, height = 400, 160
    image = Image.new("RGB", (width, height), (255, 255, 255))
    draw = ImageDraw.Draw(image)

    try:
        font = ImageFont.truetype("arial.ttf", 70)
    except:
        font = ImageFont.load_default()

    spacing = width // (len(text) + 1)
    char_positions = []

    # ===== วาดตัวอักษร =====
    for i, char in enumerate(text):
        x = spacing * (i + 1) - 25
        y = random.randint(35, 55)

        char_positions.append((x, y))

        draw.text(
            (x, y),
            char,
            font=font,
            fill=(0, 0, 0)
        )

    # ===== เส้นสุ่มทั่วภาพ (เพิ่มเยอะ) =====
    for _ in range(12):
        draw.line(
            (
                random.randint(0, width),
                random.randint(0, height),
                random.randint(0, width),
                random.randint(0, height),
            ),
            fill=(
                random.randint(80, 150),
                random.randint(80, 150),
                random.randint(80, 150),
            ),
            width=random.randint(1, 3),
        )

    # ===== เส้นพาดตัดตัวอักษรแต่ละตัว =====
    for (x, y) in char_positions:
        draw.line(
            (
                x - 15,
                y + random.randint(10, 40),
                x + 70,
                y + random.randint(10, 40),
            ),
            fill=(
                random.randint(50, 120),
                random.randint(50, 120),
                random.randint(50, 120),
            ),
            width=3,
        )

    # ===== เส้นโค้งมั่ว ๆ =====
    for _ in range(6):
        draw.arc(
            (
                random.randint(0, width - 100),
                random.randint(0, height - 100),
                random.randint(100, width),
                random.randint(80, height),
            ),
            start=random.randint(0, 360),
            end=random.randint(0, 360),
            fill=(
                random.randint(100, 180),
                random.randint(100, 180),
                random.randint(100, 180),
            ),
            width=2,
        )

    # ===== Noise หนาแน่น =====
    for _ in range(400):
        draw.point(
            (random.randint(0, width), random.randint(0, height)),
            fill=(
                random.randint(120, 200),
                random.randint(120, 200),
                random.randint(120, 200),
            ),
        )

    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    buffer.seek(0)
    return buffer


# ===== MODAL =====

class CaptchaModal(Modal):
    def __init__(self, role):
        super().__init__(title="กรอกรหัสยืนยัน")
        self.role = role

        self.answer = TextInput(
            label="พิมพ์ตัวเลขและตัวอักษรให้ถูกต้อง",
            max_length=8,
        )
        self.add_item(self.answer)

    async def on_submit(self, interaction: discord.Interaction):

        user_id = interaction.user.id

        if user_id not in captcha_cache:
            await interaction.response.send_message(
                "🍒 คุณยังไม่ได้กดสุ่มรหัส",
                ephemeral=True
            )
            return

        correct_code = captcha_cache[user_id]

        if self.answer.value.upper() == correct_code:
            await interaction.user.add_roles(self.role)
            del captcha_cache[user_id]

            await interaction.response.send_message(
                f"🍃 สำเร็จ ได้รับยศ {self.role.mention}",
                ephemeral=True
            )
        else:
            await interaction.response.send_message(
                "💢 รหัสไม่ถูกต้อง กดสุ่มใหม่อีกครั้ง",
                ephemeral=True
            )


# ===== VIEW =====

class VerifyView(View):
    def __init__(self, role):
        super().__init__(timeout=None)
        self.role = role

    # ปุ่มที่ 1: สุ่มรหัส
    @discord.ui.button(label="สุ่มรหัส", style=discord.ButtonStyle.blurple, emoji="🍲")
    async def generate(self, interaction: discord.Interaction, button: Button):

        text = generate_text()
        captcha_cache[interaction.user.id] = text

        image_buffer = generate_image(text)
        file = discord.File(image_buffer, filename="captcha.png")

        embed = discord.Embed(
            title="🔐 System | Verify",
            description="ใส่ตัวเลขเเละตัวอักษรให้ถูกเพื่อรับยศ",
            color=discord.Color.red(),
        )
        embed.set_image(url="attachment://captcha.png")

        await interaction.response.send_message(
            embed=embed,
            file=file,
            ephemeral=True,
        )

    # ปุ่มที่ 2: กรอกรหัส
    @discord.ui.button(label="กรอกรหัส", style=discord.ButtonStyle.green, emoji="📁")
    async def input_code(self, interaction: discord.Interaction, button: Button):

        await interaction.response.send_modal(
            CaptchaModal(self.role)
        )


# ===== COG =====

class Sayu(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="safety", description="สร้างระบบยืนยันตัวตนด้วยภาพ")
    @app_commands.checks.has_permissions(administrator=True)
    async def nobots(
        self,
        interaction: discord.Interaction,
        role: discord.Role,
        channel: discord.TextChannel,
    ):

        embed = discord.Embed(
            title="🔐 System | Verify",
            description=(
                "• กด 'สุ่มรหัส' เพื่อรับภาพ\n"
                "• กด 'กรอกรหัส' เพื่อพิมพ์คำตอบ\n"
                "• ใส่ตัวเลขให้ถูกต้องเพื่อรับยศ"
            ),
            color=discord.Color.green(),
        )

        await channel.send(embed=embed, view=VerifyView(role))

        await interaction.response.send_message(
            "🍇 สร้างระบบเรียบร้อยแล้ว",
            ephemeral=True
        )


async def setup(bot):
    await bot.add_cog(Sayu(bot))