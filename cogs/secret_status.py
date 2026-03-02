import discord
from discord.ext import commands, tasks
from discord import app_commands
from datetime import datetime, timezone, timedelta

ALLOWED_USER_ID = 1155481097753337916

class SecretStatus(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.update_status_loop = None

    # =========================
    # คำสั่งลับ ใช้ได้คนเดียว
    # =========================
    @app_commands.command(name="what_do_you_think_it_is")
    async def secret_command(self, interaction: discord.Interaction):

        if interaction.user.id != ALLOWED_USER_ID:
            await interaction.response.send_message(
                "🍅 คุณไม่มีสิทธิ์ใช้คำสั่งนี้",
                ephemeral=True
            )
            return

        # ถ้ายังไม่เริ่ม loop ให้เริ่ม
        if not self.update_status_loop:
            self.update_status_loop = self.update_status.start()

        await interaction.response.send_message(
            "✅ เปิดระบบสถานะแล้ว",
            ephemeral=True
        )

    # =========================
    # Loop อัปเดตทุก 5 วิ
    # =========================
    @tasks.loop(seconds=5)
    async def update_status(self):
        await self.bot.wait_until_ready()

        guild_count = len(self.bot.guilds)
        total_members = sum(g.member_count for g in self.bot.guilds)

        now = datetime.now(timezone(timedelta(hours=7)))

        days_th = {
            "Monday": "จันทร์",
            "Tuesday": "อังคาร",
            "Wednesday": "พุธ",
            "Thursday": "พฤหัสบดี",
            "Friday": "ศุกร์",
            "Saturday": "เสาร์",
            "Sunday": "อาทิตย์"
        }

        day_eng = now.strftime("%A")
        day_th = days_th.get(day_eng, day_eng)
        time_now = now.strftime("%H:%M:%S")

        status_text = (
            f"{guild_count}เซิร์ฟ·⌒ﾞ🍇 {total_members}คนᔕ:･ﾟ🍃 "
            f"วัน {day_th}:･ﾟ☀️ เวลา:･ﾟ({time_now})·⌒ﾞ📆"
        )

        activity = discord.Activity(
            type=discord.ActivityType.watching,
            name=status_text
        )

        await self.bot.change_presence(activity=activity)

    async def cog_unload(self):
        if self.update_status_loop:
            self.update_status.cancel()


async def setup(bot):
    await bot.add_cog(SecretStatus(bot))