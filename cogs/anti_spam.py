import discord
from discord import app_commands
from discord.ext import commands
import asyncio
import time

# ===============================
# เก็บสถานะเปิด/ปิด ต่อเซิร์ฟเวอร์
# ===============================
anti_spam_status = {}

# เก็บข้อความของแต่ละ user
user_messages = {}

# ตั้งค่าการตรวจ
SPAM_LIMIT = 5          # ส่งกี่ข้อความ
SPAM_TIME = 5           # ภายในกี่วินาที


# ===============================
# ปุ่มเปิด/ปิดระบบ
# ===============================
class AntiSpamToggleView(discord.ui.View):
    def __init__(self, guild_id):
        super().__init__(timeout=60)
        self.guild_id = guild_id

    @discord.ui.button(label="เปิดระบบ", style=discord.ButtonStyle.success, emoji="📁")
    async def enable(self, interaction: discord.Interaction, button: discord.ui.Button):
        anti_spam_status[self.guild_id] = True

        embed = discord.Embed(
            title="🛡️ ระบบป้องกันสแปม",
            description="✅ เปิดระบบป้องกันสแปมเรียบร้อยแล้ว",
            color=discord.Color.green()
        )
        await interaction.response.edit_message(embed=embed, view=None)

    @discord.ui.button(label="ปิดระบบ", style=discord.ButtonStyle.danger, emoji="💢")
    async def disable(self, interaction: discord.Interaction, button: discord.ui.Button):
        anti_spam_status[self.guild_id] = False

        embed = discord.Embed(
            title="🛡️ ระบบป้องกันสแปม",
            description="💢 ปิดระบบป้องกันสแปมเรียบร้อยแล้ว",
            color=discord.Color.red()
        )
        await interaction.response.edit_message(embed=embed, view=None)


# ===============================
# เมนูหลัก
# ===============================
class AntiSpamMainView(discord.ui.View):
    def __init__(self, guild_id):
        super().__init__(timeout=60)
        self.guild_id = guild_id

    @discord.ui.button(label="เลือกการตั้งค่า", style=discord.ButtonStyle.primary)
    async def settings(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="🛡️ ตั้งค่าระบบป้องกันสแปม",
            description="เลือกการตั้งค่าที่นี่นะคะ...",
            color=discord.Color.blue()
        )

        await interaction.response.edit_message(
            embed=embed,
            view=AntiSpamToggleView(self.guild_id)
        )


# ===============================
# Cog หลัก
# ===============================
class AntiSpam(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # ===== Slash Command =====
    @app_commands.command(name="anti-spam", description="ตั้งค่าระบบป้องกันสแปม")
    async def anti_spam(self, interaction: discord.Interaction):

        guild_id = interaction.guild.id

        if guild_id not in anti_spam_status:
            anti_spam_status[guild_id] = False

        embed = discord.Embed(
            title="📁 ตั้งค่าระบบป้องกันสแปม",
            description="สวัสดีค่ะ! เลือกตั้งค่าผ่านปุ่มด้านล่างเพื่อเปิด/ปิดระบบ",
            color=discord.Color.blurple()
        )

        embed.add_field(
            name="สถานะปัจจุบัน",
            value="📁 เปิดอยู่" if anti_spam_status[guild_id] else "💢 ปิดอยู่",
            inline=False
        )

        await interaction.response.send_message(
            embed=embed,
            view=AntiSpamMainView(guild_id),
            ephemeral=True
        )

    # ===== ระบบตรวจสแปมจริง =====
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):

        if message.author.bot:
            return

        if not message.guild:
            return

        guild_id = message.guild.id

        if not anti_spam_status.get(guild_id, False):
            return

        user_id = message.author.id
        now = time.time()

        if user_id not in user_messages:
            user_messages[user_id] = []

        user_messages[user_id].append(now)

        # ลบข้อความเก่าที่เกินเวลา
        user_messages[user_id] = [
            t for t in user_messages[user_id]
            if now - t <= SPAM_TIME
        ]

        # ถ้าเกิน limit = สแปม
        if len(user_messages[user_id]) >= SPAM_LIMIT:
            try:
                await message.delete()

                warning = await message.channel.send(
                    f"{message.author.mention} ⚠️ หยุดสแปมได้แล้ว!"
                )

                await asyncio.sleep(3)
                await warning.delete()

            except:
                pass

            user_messages[user_id] = []


# ===============================
# โหลด Cog
# ===============================
async def setup(bot):
    await bot.add_cog(AntiSpam(bot))