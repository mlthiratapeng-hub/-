import discord
from discord import app_commands
from discord.ext import commands
import random
import time
import sqlite3

class AISystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

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

        self.bad_words = ["ควาย", "โง่", "เหี้ย", "กาก", "ไอ้", "สัส", "หน้าหี", "ตอเเหล", "เย็ด", "เงี่ยน", "เสียว", "เเตก"]
        self.good_words = ["รัก", "เก่ง", "ขอบคุณ", "น่ารัก", "สวย"]

    # ===============================
    # DATABASE FUNCTIONS
    # ===============================
    def get_user(self, user_id):
        self.cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
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
    # ตรวจข้อความ
    # ===============================
    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        user = self.get_user(message.author.id)
        relationship = user[1]

        content = message.content.lower()

        # คำไม่ดี
        for word in self.bad_words:
            if word in content:
                relationship -= 20
                if relationship < 0:
                    relationship = 0

                self.update_user(message.author.id, relationship=relationship, ever_bad=1)

                embed = discord.Embed(
                    title="💔 เสียใจ...",
                    description="พูดไม่ดีเลย ความสัมพันธ์ -20",
                    color=discord.Color.red()
                )
                await message.channel.send(embed=embed)
                return

        # คำดี
        for word in self.good_words:
            if word in content:
                relationship += 3
                if relationship > 2000:
                    relationship = 2000

                self.update_user(message.author.id, relationship=relationship)

                embed = discord.Embed(
                    title="💖 ดีใจ",
                    description="พูดดีจัง ความสัมพันธ์ +3",
                    color=discord.Color.green()
                )
                await message.channel.send(embed=embed)
                return

    # ===============================
    # OPEN AI (ADMIN ONLY)
    # ===============================
    @app_commands.command(name="open_ai", description="คุยกับ Ai (แอดมินเท่านั้น)")
    @app_commands.checks.has_permissions(administrator=True)
    async def open_ai(self, interaction: discord.Interaction, message: str):

        user = self.get_user(interaction.user.id)
        relationship = user[1]

        if relationship == 0:
            return await interaction.response.send_message(
                "🛑 Ai ไม่อยากคุยกับคุณแล้ว...", ephemeral=True
            )

        if relationship < 300:
            reply = "เรายังไม่โอเคนะ..."
        elif relationship < 700:
            reply = f"อืมม... {message}"
        elif relationship < 1200:
            reply = f"😊 ฟังดูดีนะที่พูดว่า '{message}'"
        else:
            reply = f"❤️ เราชอบมากเลยที่เธอพูดว่า '{message}'"

        embed = discord.Embed(
            title="Ai ตอบกลับ",
            description=reply,
            color=discord.Color.blue()
        )

        await interaction.response.send_message(embed=embed)

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
            mood = "😊 ชอบ"
        else:
            mood = "❤️ รักเลย"

        embed = discord.Embed(
            title="💞 สถานะความสัมพันธ์",
            description=f"คะแนน: {relationship}/2000\nอารมณ์: {mood}",
            color=discord.Color.purple()
        )

        await interaction.response.send_message(embed=embed)

    # ===============================
    # BALANCE
    # ===============================
    @app_commands.command(name="balance", description="เช็คเงินของคุณ")
    async def balance(self, interaction: discord.Interaction):

        user = self.get_user(interaction.user.id)
        money = user[2]

        embed = discord.Embed(
            title="💰 กระเป๋าเงิน",
            description=f"คุณมี {money} เหรียญ",
            color=discord.Color.gold()
        )

        await interaction.response.send_message(embed=embed)

    # ===============================
    # FLOWER
    # ===============================
    @app_commands.command(name="flower", description="ซื้อดอกไม้ให้ Ai")
    async def flower(self, interaction: discord.Interaction, price: int):

        if price not in [50, 250, 500]:
            return await interaction.response.send_message("เลือกได้แค่ 50 / 250 / 500", ephemeral=True)

        user = self.get_user(interaction.user.id)
        relationship = user[1]
        money = user[2]

        if money < price:
            return await interaction.response.send_message("เงินไม่พอ585848585959559559555549555", ephemeral=True)

        relationship += price
        if relationship > 2000:
            relationship = 2000

        money -= price

        self.update_user(interaction.user.id, relationship=relationship, money=money)

        embed = discord.Embed(
            title="🌸 ให้ดอกไม้สำเร็จ",
            description=f"ความสัมพันธ์ +{price}\nตอนนี้: {relationship}/2000",
            color=discord.Color.pink()
        )

        await interaction.response.send_message(embed=embed)

    # ===============================
    # REWARD (3 ชั่วโมง)
    # ===============================
    @app_commands.command(name="reward", description="รับเงินซื้อดอกไม้ (3 ชม.)")
    async def reward(self, interaction: discord.Interaction):

        user = self.get_user(interaction.user.id)
        last_reward = user[4]
        money = user[2]

        now = time.time()

        if now - last_reward < 10800:
            remaining = int((10800 - (now - last_reward)) / 60)
            return await interaction.response.send_message(
                f"⏳ ต้องรออีก {remaining} นาทีนะค่ะ", ephemeral=True
            )

        roll = random.randint(1, 100)

        if roll <= 50:
            amount = random.randint(50, 100)
        elif roll <= 90:
            amount = random.randint(200, 400)
        else:
            amount = 500

        money += amount
        self.update_user(interaction.user.id, money=money, last_reward=now)

        embed = discord.Embed(
            title="🎁 Ai ให้รางวัล",
            description=f"คุณได้รับ {amount} เหรียญ 💰",
            color=discord.Color.green()
        )

        await interaction.response.send_message(embed=embed)


async def setup(bot):
    await bot.add_cog(AISystem(bot))