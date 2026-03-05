import discord
from discord.ext import commands, tasks
from discord import app_commands
import time

# เก็บสถานะไม่อยู่
unavailable_users = {}


# =========================
# Select เวลา
# =========================

class TimeSelect(discord.ui.Select):

    def __init__(self):

        options = [
            discord.SelectOption(label="1 ชั่วโมง", value="1"),
            discord.SelectOption(label="3 ชั่วโมง", value="3"),
            discord.SelectOption(label="5 ชั่วโมง", value="5"),
            discord.SelectOption(label="10 ชั่วโมง", value="10"),
            discord.SelectOption(label="15 ชั่วโมง", value="15"),
            discord.SelectOption(label="24 ชั่วโมง", value="24"),
            discord.SelectOption(label="ไม่มีกำหนด", value="0")
        ]

        super().__init__(
            placeholder="เลือกเวลาที่ไม่อยู่",
            options=options
        )

    async def callback(self, interaction: discord.Interaction):

        hours = int(self.values[0])

        modal = ReasonModal(hours)
        await interaction.response.send_modal(modal)


# =========================
# Modal เหตุผล
# =========================

class ReasonModal(discord.ui.Modal, title="ตั้งค่าสถานะไม่อยู่"):

    reason = discord.ui.TextInput(
        label="เหตุผลที่ไม่อยู่",
        style=discord.TextStyle.paragraph,
        placeholder="เช่น ไปเรียน / ไปทำงาน / ไม่ว่าง",
        required=True,
        max_length=200
    )

    def __init__(self, hours):
        super().__init__()
        self.hours = hours

    async def on_submit(self, interaction: discord.Interaction):

        user = interaction.user

        if self.hours == 0:
            end_time = None
            time_text = "ไม่มีกำหนด"
        else:
            end_time = time.time() + (self.hours * 3600)
            time_text = f"{self.hours} ชั่วโมง"

        unavailable_users[user.id] = {
            "reason": str(self.reason),
            "end": end_time,
            "hours": time_text
        }

        embed = discord.Embed(
            title="📴 ตั้งสถานะไม่อยู่",
            color=discord.Color.orange()
        )

        embed.add_field(
            name="👤 ผู้ใช้",
            value=user.mention,
            inline=False
        )

        embed.add_field(
            name="⏰ เวลา",
            value=time_text,
            inline=False
        )

        embed.add_field(
            name="📁 เหตุผล",
            value=self.reason,
            inline=False
        )

        embed.set_thumbnail(url=user.display_avatar.url)

        await interaction.response.send_message(embed=embed)


# =========================
# View
# =========================

class UnavailableView(discord.ui.View):

    def __init__(self):
        super().__init__(timeout=60)

        self.add_item(TimeSelect())


# =========================
# Cog
# =========================

class Unavailable(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.check_status.start()

    # =========================
    # /unavailable
    # =========================

    @app_commands.command(
        name="unavailable",
        description="ตั้งสถานะไม่อยู่"
    )
    async def unavailable(self, interaction: discord.Interaction):

        user = interaction.user

        # ถ้ามีสถานะอยู่แล้ว → ลบ
        if user.id in unavailable_users:

            unavailable_users.pop(user.id)

            embed = discord.Embed(
                title="🍧 ลบสถานะไม่อยู่",
                description=f"{user.mention} ได้ลบสถานะไม่อยู่ของคุณแล้ว",
                color=discord.Color.green()
            )

            embed.set_thumbnail(url=user.display_avatar.url)

            await interaction.response.send_message(embed=embed)

            return

        embed = discord.Embed(
            title="📴 ตั้งสถานะไม่อยู่",
            description="เลือกเวลาที่คุณจะไม่อยู่",
            color=discord.Color.blurple()
        )

        embed.set_thumbnail(url=user.display_avatar.url)

        await interaction.response.send_message(
            embed=embed,
            view=UnavailableView()
        )

    # =========================
    # ตรวจหมดเวลา
    # =========================

    @tasks.loop(minutes=1)
    async def check_status(self):

        now = time.time()

        remove_list = []

        for user_id, data in unavailable_users.items():

            end = data["end"]

            if end and now >= end:
                remove_list.append((user_id, data))

        for user_id, data in remove_list:

            user = self.bot.get_user(user_id)

            unavailable_users.pop(user_id)

            for guild in self.bot.guilds:

                member = guild.get_member(user_id)

                if member:

                    channel = guild.system_channel

                    if channel:

                        embed = discord.Embed(
                            title="🍇 หมดเวลาสถานะไม่อยู่",
                            description=f"{member.mention} ได้ทำการลบสถานะไม่อยู่ของคุณ\nเวลา: {data['hours']}",
                            color=discord.Color.green()
                        )

                        embed.set_thumbnail(url=member.display_avatar.url)

                        try:
                            await channel.send(embed=embed)
                        except:
                            pass

    @check_status.before_loop
    async def before_loop(self):
        await self.bot.wait_until_ready()


async def setup(bot):
    await bot.add_cog(Unavailable(bot))