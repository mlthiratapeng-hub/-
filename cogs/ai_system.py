import discord
from discord import app_commands
from discord.ext import commands
import random
import time
import sqlite3

class AISystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.active_channels = set()  # ห้องที่ AI เปิดอยู่

        # ===== DATABASE =====
        self.db = sqlite3.connect("ai_data.db")
        self.cursor = self.db.cursor()

        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            relationship INTEGER DEFAULT 50,
            money INTEGER DEFAULT 500,
            ever_bad INTEGER DEFAULT 0,
            last_reward REAL DEFAULT 0
        )
        """)
        self.db.commit()

        self.bad_words = ["ควาย", "โง่", "เหี้ย", "กาก", "ไอ้", "สัส", "เย็ด", "หี", "เสียว", "เงี่ยน", "ไม่ฉลาด"]
        self.good_words = ["รัก", "เก่ง", "ขอบคุณ", "น่ารัก", "เทพ"]

    # ===============================
    # DATABASE FUNCTIONS
    # ===============================
    def get_user(self, user_id):
        self.cursor.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
        user = self.cursor.fetchone()

        if user is None:
            self.cursor.execute(
                "INSERT INTO users (user_id, relationship, money, ever_bad, last_reward) VALUES (?, 50, 500, 0, 0)",
                (user_id,)
            )
            self.db.commit()
            return (user_id, 50, 500, 0, 0)

        return user

    def update_user(self, user_id, relationship=None, money=None, ever_bad=None, last_reward=None):
        if relationship is not None:
            self.cursor.execute("UPDATE users SET relationship=? WHERE user_id=?", (relationship, user_id))
        if money is not None:
            self.cursor.execute("UPDATE users SET money=? WHERE user_id=?", (money, user_id))
        if ever_bad is not None:
            self.cursor.execute("UPDATE users SET ever_bad=? WHERE user_id=?", (ever_bad, user_id))
        if last_reward is not None:
            self.cursor.execute("UPDATE users SET last_reward=? WHERE user_id=?", (last_reward, user_id))
        self.db.commit()

    # ===============================
    # เปิด AI ในห้อง
    # ===============================
    @app_commands.command(name="open_ai", description="เปิด AI ในห้องนี้")
    @app_commands.checks.has_permissions(administrator=True)
    async def open_ai(self, interaction: discord.Interaction, channel: discord.TextChannel):

        self.active_channels.add(channel.id)

        embed = discord.Embed(
            title="🍇เปิด AI สำเร็จ",
            description=f"AI จะตอบอัตโนมัติในห้อง {channel.mention}",
            color=discord.Color.green()
        )

        await interaction.response.send_message(embed=embed)

    # ===============================
    # ปิด AI
    # ===============================
    @app_commands.command(name="close_ai", description="ปิด AI ในห้องนี้")
    @app_commands.checks.has_permissions(administrator=True)
    async def close_ai(self, interaction: discord.Interaction, channel: discord.TextChannel):

        self.active_channels.discard(channel.id)

        embed = discord.Embed(
            title="🍅 ปิด AI แล้ว",
            description=f"AI จะไม่ตอบในห้อง {channel.mention}",
            color=discord.Color.red()
        )

        await interaction.response.send_message(embed=embed)

    # ===============================
    # AI ตอบอัตโนมัติ
    # ===============================
    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        if message.channel.id not in self.active_channels:
            return

        user = self.get_user(message.author.id)
        relationship = user[1]
        ever_bad = user[3]

        if relationship == 0:
            return

        content = message.content.lower()

        # ตรวจคำไม่ดี
        for word in self.bad_words:
            if word in content:
                relationship -= 20
                if relationship < 0:
                    relationship = 0
                self.update_user(message.author.id, relationship=relationship, ever_bad=1)
                await message.channel.send("💔 อย่าพูดแบบนั้นสิ...")
                return

        # ตรวจคำดี
        for word in self.good_words:
            if word in content:
                relationship += 10
                if relationship > 2000:
                    relationship = 2000
                self.update_user(message.author.id, relationship=relationship)
                await message.channel.send("💖 ดีใจจังที่พูดแบบนี้")
                return

        # ตอบปกติ
        if relationship < 300:
            reply = "เรายังไม่ค่อยโอเคนะ..."
        elif relationship < 700:
            reply = f"อืม... {message.content}"
        elif relationship < 1200:
            reply = f"😊 ฟังดูดีนะ"
        else:
            reply = f"❤️ เราชอบที่เธอพูดแบบนั้น"

        # ถ้ามีรูปแนบมา
        if message.attachments:
            reply += "\n📷 ฮั่นเเน่"

        await message.channel.send(reply)

    # ===============================
    # STATUS
    # ===============================
    @app_commands.command(name="status", description="ดูสถานะความสัมพันธ์")
    async def status(self, interaction: discord.Interaction):

        user = self.get_user(interaction.user.id)
        relationship = user[1]
        ever_bad = user[3]

        if relationship == 50 and ever_bad == 0:
            mood = "👋 คนรู้จัก"
        elif relationship < 300:
            mood = "😐 เฉยๆ" if ever_bad == 0 else "😡 เกลียดมาก"
        elif relationship < 700:
            mood = "😐 เฉยๆ"
        elif relationship < 1200:
            mood = "😊 ชอบนะ"
        else:
            mood = "❤️ รักเลย"

        embed = discord.Embed(
            title="💞 สถานะความสัมพันธ์",
            description=f"คะแนน: {relationship}/2000\nอารมณ์: {mood}",
            color=discord.Color.purple()
        )

        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(AISystem(bot))