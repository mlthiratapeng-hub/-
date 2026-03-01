import discord
from discord.ext import commands
from discord import app_commands
from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()

OPENAI_KEY = os.getenv("OPENAI_KEY")
client_ai = OpenAI(api_key=OPENAI_KEY)

class AISystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.ai_channel_id = None
        self.memory = {}  # เก็บบทสนทนาต่อ user

    # =============================
    # เลือกห้องให้ AI ทำงาน
    # =============================
    @app_commands.command(name="open_ai", description="เลือกห้องที่ AI จะอยู่")
    @app_commands.checks.has_permissions(administrator=True)
    async def open_ai(self, interaction: discord.Interaction, channel: discord.TextChannel):
        self.ai_channel_id = channel.id
        await interaction.response.send_message(
            f"✅ เปิด AI ในห้อง {channel.mention} เรียบร้อย",
            ephemeral=True
        )

    # =============================
    # ฟังทุกข้อความในห้อง AI
    # =============================
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return

        if self.ai_channel_id is None:
            return

        if message.channel.id != self.ai_channel_id:
            return

        async with message.channel.typing():

            user_id = message.author.id

            if user_id not in self.memory:
                self.memory[user_id] = []

            # เพิ่มข้อความ user เข้า memory
            self.memory[user_id].append({
                "role": "user",
                "content": message.content
            })

            # จำกัด context ไม่ให้ยาวเกิน
            self.memory[user_id] = self.memory[user_id][-8:]

            try:
                response = client_ai.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {
                            "role": "system",
                            "content": "คุณคือ AI ผู้ช่วยเก่งเรื่องโค้ด พูดธรรมชาติ ไม่เยิ่นเย้อ"
                        },
                        *self.memory[user_id]
                    ],
                    temperature=0.7
                )

                reply_text = response.choices[0].message.content

                # เพิ่มคำตอบเข้า memory
                self.memory[user_id].append({
                    "role": "assistant",
                    "content": reply_text
                })

                await message.reply(reply_text)

            except Exception as e:
                await message.reply("⚠️ AI มีปัญหา ลองใหม่อีกครั้ง")
                print("AI ERROR:", e)


async def setup(bot):
    await bot.add_cog(AISystem(bot))