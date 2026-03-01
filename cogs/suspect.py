import discord
from discord.ext import commands
from discord import app_commands
from discord.ui import View, Button, Modal, TextInput, Select
from PIL import Image, ImageDraw, ImageFont
import random
import string
import io

MAIN_GUILD_ID = 1476624073990738022
CAPTCHA_LENGTH = 6


# ================= CAPTCHA =================

def generate_captcha_text():
    chars = string.ascii_uppercase + string.digits
    return "".join(random.choice(chars) for _ in range(CAPTCHA_LENGTH))


def generate_captcha_image(text):
    width, height = 320, 120
    image = Image.new("RGB", (width, height), (255, 255, 255))
    draw = ImageDraw.Draw(image)

    try:
        font = ImageFont.truetype("arial.ttf", 55)
    except:
        font = ImageFont.load_default()

    for i, char in enumerate(text):
        x = 30 + i * 45 + random.randint(-5, 5)
        y = 30 + random.randint(-10, 10)
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

    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    buffer.seek(0)
    return buffer


# ================= MODAL =================

class CaptchaModal(Modal):
    def __init__(self, correct_text, role: discord.Role):
        super().__init__(title="Identity Verification")
        self.correct_text = correct_text
        self.role = role

        self.answer = TextInput(
            label="พิมพ์ตัวอักษรตามภาพ",
            max_length=CAPTCHA_LENGTH,
        )
        self.add_item(self.answer)

    async def on_submit(self, interaction: discord.Interaction):
        if self.answer.value.upper() == self.correct_text:
            try:
                await interaction.user.add_roles(self.role)
                embed = discord.Embed(
                    title="🍃 ยืนยันสำเร็จ",
                    description=f"คุณได้รับยศ {self.role.mention}",
                    color=discord.Color.green(),
                )
            except:
                embed = discord.Embed(
                    title="⚠ บอทให้ยศไม่ได้",
                    description="เช็คว่า role บอทสูงกว่ายศที่ให้",
                    color=discord.Color.orange(),
                )
        else:
            embed = discord.Embed(
                title="🍓 รหัสไม่ถูกต้อง",
                color=discord.Color.red(),
            )

        await interaction.response.send_message(embed=embed, ephemeral=True)


# ================= ROLE SELECT =================

class RoleSelect(Select):
    def __init__(self, roles):
        options = [
            discord.SelectOption(label=role.name, value=str(role.id))
            for role in roles[:25]
        ]

        super().__init__(
            placeholder="เลือกยศที่จะให้เมื่อยืนยันสำเร็จ",
            options=options,
        )

    async def callback(self, interaction: discord.Interaction):
        role_id = int(self.values[0])
        role = interaction.guild.get_role(role_id)

        captcha_text = generate_captcha_text()
        image_buffer = generate_captcha_image(captcha_text)
        file = discord.File(image_buffer, filename="captcha.png")

        embed = discord.Embed(
            title="🔐 Identity Verification",
            description="กรอกรหัสตามภาพ แล้วกดส่ง",
            color=discord.Color.blurple(),
        )
        embed.set_image(url="attachment://captcha.png")

        await interaction.response.send_message(
            embed=embed,
            file=file,
        )

        await interaction.followup.send_modal(
            CaptchaModal(captcha_text, role)
        )


class RoleSelectView(View):
    def __init__(self, roles):
        super().__init__(timeout=180)
        self.add_item(RoleSelect(roles))


# ================= COG =================

class Suspect(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="suspect",
        description="ระบบยืนยันตัวตนด้วยภาพ",
    )
    async def verify_identity(self, interaction: discord.Interaction):

        # ต้องเป็นแอดมินเซิร์ฟปลายทาง
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message(
                "🍎ใช้ได้เฉพาะแอดมินของเซิร์ฟนี้",
                ephemeral=True,
            )
            return

        # ต้องอยู่ในเซิร์ฟหลัก
        main_guild = self.bot.get_guild(MAIN_GUILD_ID)
        if not main_guild or not main_guild.get_member(interaction.user.id):
            await interaction.response.send_message(
                "🥩คุณต้องอยู่ในเซิร์ฟหลักก่อน",
                ephemeral=True,
            )
            return

        # ดึง role ที่บอทสามารถให้ได้
        roles = [
            r
            for r in interaction.guild.roles
            if r < interaction.guild.me.top_role and not r.is_default()
        ]

        if not roles:
            await interaction.response.send_message(
                "💢ไม่มียศที่บอทให้ได้",
                ephemeral=True,
            )
            return

        embed = discord.Embed(
            title="🛡 ระบบยืนยันตัวตน",
            description="เลือกยศที่ต้องการให้หลังยืนยัน",
            color=discord.Color.blue(),
        )

        await interaction.response.send_message(
            embed=embed,
            view=RoleSelectView(roles),
        )


async def setup(bot):
    await bot.add_cog(Suspect(bot))