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
        font = ImageFont.truetype("arial.ttf", 70)
    except:
        font = ImageFont.load_default()

    spacing = width // (len(text) + 1)
    char_boxes = []

    # ===== วาดตัวอักษร =====
    for i, char in enumerate(text):
        x = spacing * (i + 1)
        y = random.randint(55, 65)

        char_layer = Image.new("RGBA", (140, 140), (255, 255, 255, 0))
        char_draw = ImageDraw.Draw(char_layer)

        char_draw.text((40, 25), char, font=font, fill=(0, 0, 0))

        angle = random.randint(-12, 12)
        rotated = char_layer.rotate(angle, resample=Image.BICUBIC, expand=True)

        paste_x = x - rotated.width // 2
        paste_y = y - rotated.height // 2

        image.paste(rotated, (paste_x, paste_y), rotated)

        # เก็บกรอบคร่าว ๆ ของตัวอักษร
        char_boxes.append((
            paste_x,
            paste_y,
            paste_x + rotated.width,
            paste_y + rotated.height
        ))

    # ===================================================
    # 🔥 เส้นตัดทับตัวอักษรจริง อย่างน้อย 2 เส้น
    # ===================================================

    chosen_boxes = random.sample(char_boxes, 2)

    for box in chosen_boxes:
        x1, y1, x2, y2 = box

        center_y = (y1 + y2) // 2

        # เส้นพาดทะลุตัวอักษรแนวนอน
        draw.line(
            (x1 - 20, center_y, x2 + 20, center_y + random.randint(-5, 5)),
            fill=(random.randint(60,120), random.randint(60,120), random.randint(60,120)),
            width=4
        )

    # ===================================================
    # 🔥 เพิ่มเส้นสุ่มอีก 1-3 เส้น (อาจจะตัดหลายตัว)
    # ===================================================
    extra_lines = random.randint(1, 3)

    for _ in range(extra_lines):
        start_x = random.randint(0, width // 3)
        end_x = random.randint(width // 2, width)

        start_y = random.randint(60, 100)
        end_y = random.randint(60, 100)

        draw.line(
            (start_x, start_y, end_x, end_y),
            fill=(random.randint(80,150), random.randint(80,150), random.randint(80,150)),
            width=3
        )

    # ===================================================
    # Noise เบา ๆ
    # ===================================================
    for _ in range(150):
        draw.point(
            (random.randint(0, width), random.randint(0, height)),
            fill=(random.randint(170, 220),
                  random.randint(170, 220),
                  random.randint(170, 220)),
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