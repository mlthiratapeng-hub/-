import discord
from discord import app_commands
from discord.ext import commands
import sqlite3
import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

OPENAI_KEY = os.getenv("OPENAI_KEY")

if not OPENAI_KEY:
    print("❌ OPENAI_KEY NOT FOUND")

client = OpenAI(api_key=OPENAI_KEY)


class AISystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.active_channels = set()
        self.memory = {}

        # ===== DATABASE =====
        self.db = sqlite3.connect("ai_data.db")
        self.cursor = self.db.cursor()
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            relationship INTEGER DEFAULT 50
        )
        """)
        self.db.commit()

    # ==========================
    # DATABASE
    # ==========================
    def get_user(self, user_id):
        self.cursor.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
        user = self.cursor.fetchone()

        if user is None:
            self.cursor.execute(
                "INSERT INTO users (user_id, relationship) VALUES (?, 50)",
                (user_id,)
            )
            self.db.commit()
            return (user_id, 50)

        return user

    # ==========================
    # เปิด / ปิด AI
    # ==========================
    @app_commands.command(name="open_ai", description="เปิด AI ในห้อง")
    @app_commands.checks.has_permissions(administrator=True)
    async def open_ai(self, interaction: discord.Interaction, channel: discord.TextChannel):
        self.active_channels.add(channel.id)
        await interaction.response.send_message(
            f"🤖 AI เปิดใน {channel.mention}", ephemeral=True
        )

    @app_commands.command(name="close_ai", description="ปิด AI")
    @app_commands.checks.has_permissions(administrator=True)
    async def close_ai(self, interaction: discord.Interaction, channel: discord.TextChannel):
        self.active_channels.discard(channel.id)
        await interaction.response.send_message("🔴 ปิด AI แล้ว", ephemeral=True)

    # ==========================
    # GENERATE AI
    # ==========================
    async def generate_reply(self, message, relationship):

        user_id = message.author.id

        if relationship < 20:
            mood = "หงุดหงิด พูดสั้น ๆ"
        elif relationship < 50:
            mood = "เฉย ๆ"
        elif relationship < 100:
            mood = "เป็นมิตร"
        else:
            mood = "สนิทมาก"

        if user_id not in self.memory:
            self.memory[user_id] = []

        self.memory[user_id].append({
            "role": "user",
            "content": message.content
        })

        self.memory[user_id] = self.memory[user_id][-6:]

        content = [
            {"type": "text", "text": message.content}
        ]

        for attach in message.attachments:
            if attach.content_type and "image" in attach.content_type:
                content.append({
                    "type": "image_url",
                    "image_url": {"url": attach.url}
                })

        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": f"""
คุณคือ VEX AI
บุคลิก: {mood}
คะแนนความสัมพันธ์: {relationship}
ตอบแบบธรรมชาติ ไม่ยาวเกินไป
"""
                    },
                    *self.memory[user_id],
                    {
                        "role": "user",
                        "content": content
                    }
                ],
                temperature=0.8
            )

            reply_text = response.choices[0].message.content

        except Exception as e:
            print("🔥 OPENAI ERROR:", e)
            return "⚠️ ระบบ AI ขัดข้อง"

        self.memory[user_id].append({
            "role": "assistant",
            "content": reply_text
        })

        self.memory[user_id] = self.memory[user_id][-6:]

        return reply_text

    # ==========================
    # AUTO REPLY
    # ==========================
    @commands.Cog.listener()
    async def on_message(self, message):

        if message.author.bot:
            return

        if message.channel.id not in self.active_channels:
            return

        user = self.get_user(message.author.id)
        relationship = user[1]

        if relationship <= 0:
            return

        try:
            async with message.channel.typing():
                reply = await self.generate_reply(message, relationship)
                await message.channel.send(reply)

        except Exception as e:
            print("🔥 AI LISTENER ERROR:", e)
            await message.channel.send("⚠️ AI มีปัญหา")


async def setup(bot):
    await bot.add_cog(AISystem(bot))