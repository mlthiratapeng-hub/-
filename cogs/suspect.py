import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import View, Button, Modal, TextInput, Select
from PIL import Image, ImageDraw, ImageFont
import random
import string
import io

GUILD_REQUIRED_ID = 1476624073990738022
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

    for i, char in enumerate(text):
        x = 30 + i * 45 + random.randint(-5, 5)
        y = 30 + random.randint(-10, 10)
        color = (
            random.randint(0, 150),
            random.randint(0, 150),
            random.randint(0, 150)
        )
        draw.text((x, y), char, font=font, fill=color)

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

    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    buffer.seek(0)
    return buffer


# ================= MODAL =================

class CaptchaModal(Modal):
    def __init__(self, correct_text, selected_role: discord.Role):
        super().__init__(title="Report For Duty Verification")
        self.correct_text = correct_text
        self.selected_role = selected_role

        self.answer = TextInput(
            label="พิมพ์ตัวอักษรและตัวเลขตามภาพ",
            max_length=CAPTCHA_LENGTH,
            required=True
        )
        self.add_item(self.answer)

    async def on_submit(self, interaction: discord.Interaction):

        if self.answer.value.upper() == self.correct_text:

            try:
                await interaction.user.add_roles(self.selected_role)

                embed = discord.Embed(
                    title="🍇 Verification Successful",
                    description=f"คุณได้รับยศ {self.selected_role.mention} เรียบร้อยแล้ว",
                    color=discord.Color.green()
                )

            except:
                embed = discord.Embed(
                    title="⚠ Error",
                    description="บอทไม่มีสิทธิ์ให้ยศนี้ (เช็ค role hierarchy)",
                    color=discord.Color.orange()
                )
        else:
            embed = discord.Embed(
                title="🍎 Verification Failed",
                description="ตัวอักษรไม่ถูกต้อง",
                color=discord.Color.red()
            )

        await interaction.response.send_message(embed=embed, ephemeral=True)


# ================= VIEW =================

class RoleSelect(Select):
    def __init__(self, roles, captcha_text):
        options = [
            discord.SelectOption(
                label=role.name,
                value=str(role.id)
            )
            for role in roles[:25]
        ]

        super().__init__(
            placeholder="เลือกยศที่ต้องการให้หลังยืนยัน",
            options=options
        )

        self.captcha_text = captcha_text

    async def callback(self, interaction: discord.Interaction):
        role = interaction.guild.get_role(int(self.values[0]))

        await interaction.response.send_modal(
            CaptchaModal(self.captcha_text, role)
        )


class VerifyView(View):
    def __init__(self, bot):
        super().__init__(timeout=300)
        self.bot = bot

    @discord.ui.button(label="Report For Duty", style=discord.ButtonStyle.green)
    async def verify(self, interaction: discord.Interaction, button: Button):

        # ต้องเป็นแอดมิน
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message(
                "🌶️ ใช้ได้เฉพาะแอดมิน",
                ephemeral=True
            )
            return

        # ต้องอยู่ดิสหลัก
        required_guild = self.bot.get_guild(GUILD_REQUIRED_ID)
        if not required_guild or not required_guild.get_member(interaction.user.id):
            await interaction.response.send_message(
                "💢 คุณต้องอยู่ในดิสหลักก่อนถึงใช้คำสั่งนี้ได้",
                ephemeral=True
            )
            return

        captcha_text = generate_captcha_text()
        image_buffer = generate_captcha_image(captcha_text)
        file = discord.File(image_buffer, filename="captcha.png")

        # ดึง role ที่บอทสามารถให้ได้
        roles = [
            role for role in interaction.guild.roles
            if role < interaction.guild.me.top_role and not role.is_default()
        ]

        view = View(timeout=120)
        view.add_item(RoleSelect(roles, captcha_text))

        embed = discord.Embed(
            title="🔐 Identity Verification",
            description="1️⃣ เลือกยศ\n2️⃣ กรอก captcha",
            color=discord.Color.blurple()
        )
        embed.set_image(url="attachment://captcha.png")

        await interaction.response.send_message(
            embed=embed,
            file=file,
            view=view,
            ephemeral=True
        )


# ================= COG =================

class ReportForDuty(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="confirm", description="ระบบยืนยันตัวตนด้วยภาพ")
    async def confirm(self, interaction: discord.Interaction):

        embed = discord.Embed(
            title="🛡 Report For Duty System",
            description="กดปุ่มด้านล่างเพื่อเริ่มระบบ",
            color=discord.Color.blue()
        )

        await interaction.response.send_message(
            embed=embed,
            view=VerifyView(self.bot)
        )


async def setup(bot):
    await bot.add_cog(ReportForDuty(bot))