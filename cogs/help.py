import discord
from discord.ext import commands
from discord import app_commands


OWNER_ID = 1127935823195668480


class Help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="help", description="ดูข้อมูลคำสั่งทั้งหมดของบอท")
    async def help_command(self, interaction: discord.Interaction):

        owner = self.bot.get_user(OWNER_ID)
        if not owner:
            owner = await self.bot.fetch_user(OWNER_ID)

        embed = discord.Embed(
            title="✨ ระบบคำสั่งทั้งหมดของบอท",
            description="📌 รวมคำสั่งความปลอดภัยและจัดการเซิร์ฟเวอร์",
            color=discord.Color.from_rgb(88, 101, 242)
        )

        # 👤 โปรไฟล์เจ้าของ
        embed.set_author(
            name=f"Owner: {owner}",
            icon_url=owner.display_avatar.url
        )

        embed.set_thumbnail(url=interaction.guild.icon.url if interaction.guild.icon else None)

        # ===== หมวด Security =====
        embed.add_field(
            name="🛡️ ระบบป้องกัน",
            value=(
                "`/protect_link` ป้องกันลิงก์\n"
                "`/protect_spam` ป้องกันสแปม\n"
                "`/protect_nuke` ป้องกันยิงดิส\n"
                "`/safety` ยืนยันตัวตนด้วยภาพ\n"
                "`/verify_identity` ยืนยันตัวตนด้วยเลข\n"
                "`/noplss` ป้องกันการตรวจสอบจากบอท\n"
                "`/cyber` เช็คลิ้งแบบมาตรฐานgoogle"
            ),
            inline=False
        )

        # ===== หมวด Moderation =====
        embed.add_field(
            name="🔨 ระบบจัดการ",
            value=(
                "`/kick` เตะสมาชิก\n"
                "`/ban` แบนสมาชิก\n"
                "`/delete` ลบข้อความตามจำนวน\n"
                "`/rank` ให้ยศ\n"
                "`/wecome` เซ็ตติ้งwecomeตอนคนเข้า\n"
                "`/goodbey` เซ็ตติ้งตอนคนออก\n"
                "`/webhook` พวกคำสั่งนี้จะเป็นเกี่ยวกับwebhook\n"
                "`/invitation_set` เซ็ตคำเชิญ\n"
                "`/release` ปลดยศ\n"
                "`/system` ปิดการใช้แอพภายนอกทุกห้อง\n"
                "`/out_of_time` หมดเวลาสมาชิก"
            ),
            inline=False
        )

        # ===== หมวด Utility =====
        embed.add_field(
            name="⚙️ ระบบเสริม",
            value=(
                "`/check_operation` เช็คการทำงานบอท\n"
                "`/logall` ตรวจสอบการเคลื่อนไหว\n"
                "`/setbackup` เซ็ตโครงสร้างเซิร์ฟ\n"
                "`/please_tell_them` ฝากบอก\n"
                "`/restore` กู้คืนข้อมูลจาก backup\n"
                "`/server` บอกข้อมูลเซิฟเวอร์นี้\n"
                "`/ticket` สร้างห้องแจ้งปัญหา\n"
                "`/joice` ให้บอทจอยโดยไม่ออกไปไหนเลย\n"
                "`/unavailable` ตั้งสถานะว่าไม่อยู่\n"
                "`/specify_bot_user` สร้างห้องบอทคนเเละบอท\n"
                "`/invitation_set` เช็คคำเชิญ"
            ),
            inline=False
        )

        embed.set_footer(text="Bot Security System • All Commands")

        await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot):
    await bot.add_cog(Help(bot))