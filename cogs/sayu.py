import discord
from discord.ext import commands
from discord import app_commands
from discord.ui import View, Button, Modal, TextInput
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import random
import string
import io

# ================= CAPTCHA =================

def generate_text():
    length = random.randint(4, 8)
    chars = string.ascii_uppercase + string.digits
    return "".join(random.choice(chars) for _ in range(length))


def generate_image(text):
    width, height = 350, 130
    image = Image.new("RGB", (width, height), (255, 255, 255))
    draw = ImageDraw.Draw(image)

    try:
        font = ImageFont.truetype("arial.ttf", 60)
    except:
        font = ImageFont.load_default()

    # วาดตัวหนังสือแบบเละ ๆ
    for i, char in enumerate(text):
        x = 30 + i * 40 + random.randint(-10, 10)
        y = 30 + random.randint(-15, 15)

        draw.text(
            (x, y),
            char,
            font=font,
            fill=(
                random.randint(0, 150),
                random.randint(0, 150),
                random.randint(0, 150),
            ),
        )

    # เส้นกวนตา
    for _ in range(8):
        draw.line(
            (
                random.randint(0, width),
                random.randint(0, height),
                random.randint(0, width),
                random.randint(0, height),
            ),
            fill=(
                random.randint(0, 255),
                random.randint(0, 255),
                random.randint(0, 255),
            ),
            width=3,
        )

    # จุด noise
    for _ in range(500):
        draw.point(
            (random.randint(0, width), random.randint(0, height)),
            fill=(0, 0, 0),
        )

    image = image.filter(ImageFilter.GaussianBlur(1))

    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    buffer.seek(0)
    return buffer


# ================= MODAL =================

class CaptchaModal(Modal):
    def __init__(self, text, role: discord.Role):
        super().__init__(title="Verify Yourself")
        self.correct = text
        self.role = role

        self.input = TextInput(
            label="พิมพ์ตัวอักษรตามภาพ",
            max_length=8,
        )
        self.add_item(self.input)

    async def on_submit(self, interaction: discord.Interaction):

        if self.input.value.upper() == self.correct:
            try:
                await interaction.user.add_roles(self.role)
                embed = discord.Embed(
                    title="🌶️ สำเร็จ",
                    description=f"ได้รับยศ {self.role.mention}",
                    color=discord.Color.green(),
                )
            except:
                embed = discord.Embed(
                    title="⚠ บอทให้ยศไม่ได้",
                    description="เช็คตำแหน่งยศบอท",
                    color=discord.Color.orange(),
                )
        else:
            embed = discord.Embed(
                title="💢 ไม่ถูกต้อง",
                description="กดปุ่มใหม่เพื่อรับรหัสใหม่",
                color=discord.Color.red(),
            )

        await interaction.response.send_message(embed=embed, ephemeral=True)


# ================= VIEW =================

class VerifyView(View):
    def __init__(self, role: discord.Role):
        super().__init__(timeout=None)
        self.role = role

    @discord.ui.button(label="Verify", style=discord.ButtonStyle.green, emoji="🍇")
    async def verify(self, interaction: discord.Interaction, button: Button):

        text = generate_text()
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

        await interaction.followup.send_modal(
            CaptchaModal(text, self.role)
        )


# ================= COG =================

class Sayu(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="safety", description="สร้างระบบกันบอท")
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
                "• กดปุ่มด้านล่างเพื่อยืนยันตัวตน\n"
                "• ระบบจะสุ่มรหัสใหม่ทุกครั้งที่กด\n"
                "• ใส่ตัวเลขให้ถูกต้องเพื่อรับยศ"
            ),
            color=discord.Color.green(),
        )

        view = VerifyView(role)

        await channel.send(embed=embed, view=view)

        await interaction.response.send_message(
            "สร้างระบบเรียบร้อยแล้ว",
            ephemeral=True,
        )


async def setup(bot):
    await bot.add_cog(Sayu(bot))