import discord
from discord import app_commands
from discord.ext import commands
import time
import re

anti_spam_status = {}

# เก็บข้อมูล spam
user_message_log = {}
user_attachment_log = {}
user_gif_log = {}

# ================= TOGGLE VIEW =================

class AntiSpamToggleView(discord.ui.View):
    def __init__(self, guild_id: int):
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


# ================= MAIN VIEW =================

class AntiSpamMainView(discord.ui.View):
    def __init__(self, guild_id: int):
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


# ================= COG =================

class AntiSpam(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # ===== SLASH COMMAND =====

    @app_commands.command(name="anti-spam", description="ตั้งค่าระบบป้องกันสแปม")
    async def anti_spam(self, interaction: discord.Interaction):

        if not interaction.guild:
            return

        guild_id = interaction.guild.id

        if guild_id not in anti_spam_status:
            anti_spam_status[guild_id] = False

        embed = discord.Embed(
            title="📁 ตั้งค่าระบบป้องกันสแปม",
            description="เลือกตั้งค่าผ่านปุ่มด้านล่างเพื่อเปิด/ปิดระบบ",
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

    # ================= SPAM DETECTION =================

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):

        if not message.guild:
            return

        if message.author.bot:
            return

        guild_id = message.guild.id

        if not anti_spam_status.get(guild_id):
            return

        user_id = message.author.id
        now = time.time()

        # ===== MESSAGE SPAM =====

        if user_id not in user_message_log:
            user_message_log[user_id] = []

        user_message_log[user_id].append(now)
        user_message_log[user_id] = [t for t in user_message_log[user_id] if now - t < 5]

        if len(user_message_log[user_id]) > 5:
            await message.delete()

            warn = await message.channel.send(
                f"🍉 {message.author.mention} หยุดสแปมข้อความ"
            )
            await warn.delete(delay=3)
            return

        # ===== EMOJI SPAM =====

        emoji_count = len(re.findall(r'<a?:\w+:\d+>', message.content))
        emoji_count += len(re.findall(r'[\U0001F600-\U0001F64F]', message.content))

        if emoji_count > 6:

            await message.delete()

            warn = await message.channel.send(
                f"🌶️ {message.author.mention} หยุดสแปมอีโมจิ"
            )
            await warn.delete(delay=3)
            return

        # ===== FILE / IMAGE SPAM =====

        if message.attachments:

            if user_id not in user_attachment_log:
                user_attachment_log[user_id] = []

            user_attachment_log[user_id].append(now)
            user_attachment_log[user_id] = [
                t for t in user_attachment_log[user_id] if now - t < 10
            ]

            if len(user_attachment_log[user_id]) > 3:

                await message.delete()

                warn = await message.channel.send(
                    f"💣 {message.author.mention} หยุดสแปมไฟล์หรือรูป"
                )
                await warn.delete(delay=3)
                return

        # ===== GIF SPAM =====

        is_gif = False

        # เช็คไฟล์ gif
        for att in message.attachments:
            if att.filename.lower().endswith(".gif"):
                is_gif = True

        # เช็คลิงก์ gif
        if ".gif" in message.content.lower():
            is_gif = True

        # เช็ค tenor / giphy
        if "tenor.com" in message.content.lower() or "giphy.com" in message.content.lower():
            is_gif = True

        if is_gif:

            if user_id not in user_gif_log:
                user_gif_log[user_id] = []

            user_gif_log[user_id].append(now)
            user_gif_log[user_id] = [t for t in user_gif_log[user_id] if now - t < 10]

            if len(user_gif_log[user_id]) > 3:

                await message.delete()

                warn = await message.channel.send(
                    f"🕸️ {message.author.mention} หยุดสแปม GIF"
                )
                await warn.delete(delay=3)
                return


async def setup(bot):
    await bot.add_cog(AntiSpam(bot))