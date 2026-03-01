import discord
from discord.ext import commands
from discord import app_commands
from discord.ui import View, Button, Modal, TextInput
from PIL import Image, ImageDraw, ImageFont
import random
import string
import io

captcha_cache = {}

# ===== CAPTCHA =====

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
    char_boxes = []

    # ===== วาดตัวอักษร =====
    for i, char in enumerate(text):
        x = spacing * (i + 1)
        y = random.randint(65, 85)

        draw.text(
            (x, y),
            char,
            font=font,
            fill=(0, 0, 0),
            anchor="mm",
            stroke_width=2,
            stroke_fill=(255, 255, 255),
        )

        bbox = draw.textbbox((x, y), char, font=font, anchor="mm")
        char_boxes.append(bbox)

    # ===================================================
    # 🔥 เส้นกินประมาณ 1/3 ของตัวอักษร (2-3 ตัว)
    # ===================================================

    chosen_boxes = random.sample(char_boxes, min(random.randint(2, 3), len(char_boxes)))

    for box in chosen_boxes:
        x1, y1, x2, y2 = box
        height_box = y2 - y1

        # เลือกช่วงล่างประมาณ 25-40%
        start_y = y2 - int(height_box * random.uniform(0.35, 0.45))
        end_y = start_y + random.randint(3, 8)

        draw.line(
            (x1 - 5, start_y, x2 + 5, end_y),
            fill=(random.randint(60, 100),
                  random.randint(60, 100),
                  random.randint(60, 100)),
            width=random.randint(4, 8),
        )

    # ===================================================
    # 🔥 เส้นมั่วทั่วภาพ (5-8 เส้น)
    # ===================================================

    for _ in range(random.randint(5, 8)):
        draw.line(
            (
                random.randint(0, width),
                random.randint(0, height),
                random.randint(0, width),
                random.randint(0, height),
            ),
            fill=(random.randint(80, 160),
                  random.randint(80, 160),
                  random.randint(80, 160)),
            width=random.randint(2, 5),
        )

    # ===================================================
    # Noise กลาง ๆ
    # ===================================================

    for _ in range(400):
        draw.point(
            (random.randint(0, width - 1),
             random.randint(0, height - 1)),
            fill=(
                random.randint(170, 220),
                random.randint(170, 220),
                random.randint(170, 220),
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
            max_length=6,
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
                f"🫒 สำเร็จ ได้รับยศ {self.role.mention}",
                ephemeral=True
            )
        else:
            await interaction.response.send_message(
                "🌶️ รหัสไม่ถูกต้อง กดสุ่มใหม่อีกครั้ง",
                ephemeral=True
            )


# ===== VIEW =====

class VerifyView(View):
    def __init__(self, role):
        super().__init__(timeout=None)
        self.role = role

    @discord.ui.button(label="สุ่มรหัส", style=discord.ButtonStyle.blurple)
    async def generate(self, interaction: discord.Interaction, button: Button):
        await interaction.response.defer(ephemeral=True)

        text = generate_text()
        captcha_cache[interaction.user.id] = text

        image_buffer = generate_image(text)
        file = discord.File(image_buffer, filename="captcha.png")

        embed = discord.Embed(
            title="🔐 System | Verify",
            description="กดปุ่มด้านล่างเพื่อกรอกรหัสให้ถูกต้อง",
            color=discord.Color.red(),
        )
        embed.set_image(url="attachment://captcha.png")

        await interaction.followup.send(
            embed=embed,
            file=file,
            ephemeral=True,
        )

    @discord.ui.button(label="กรอกรหัส", style=discord.ButtonStyle.green)
    async def input_code(self, interaction: discord.Interaction, button: Button):
        await interaction.response.send_modal(CaptchaModal(self.role))


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
                "• ใส่ให้ถูกต้องเพื่อรับยศ"
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