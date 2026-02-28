import discord
from discord.ext import commands
from discord import app_commands
import re

# เก็บสถานะเปิด/ปิด ต่อเซิร์ฟเวอร์
anti_link_status = {}

class AntiLinkToggleView(discord.ui.View):
    def __init__(self, guild_id):
        super().__init__(timeout=60)
        self.guild_id = guild_id

    @discord.ui.button(label="เปิดระบบ", style=discord.ButtonStyle.success, emoji="📁")
    async def enable(self, interaction: discord.Interaction, button: discord.ui.Button):
        anti_link_status[self.guild_id] = True

        embed = discord.Embed(
            title="🔗 ระบบป้องกันลิงก์",
            description="📁 เปิดระบบป้องกันลิงก์เรียบร้อยแล้ว",
            color=discord.Color.green()
        )
        await interaction.response.edit_message(embed=embed, view=None)

    @discord.ui.button(label="ปิดระบบ", style=discord.ButtonStyle.danger, emoji="💢")
    async def disable(self, interaction: discord.Interaction, button: discord.ui.Button):
        anti_link_status[self.guild_id] = False

        embed = discord.Embed(
            title="🔗 ระบบป้องกันลิงก์",
            description="💢 ปิดระบบป้องกันลิงก์เรียบร้อยแล้ว",
            color=discord.Color.red()
        )
        await interaction.response.edit_message(embed=embed, view=None)


class AntiLinkMainView(discord.ui.View):
    def __init__(self, guild_id):
        super().__init__(timeout=60)
        self.guild_id = guild_id

    @discord.ui.button(label="เลือกการตั้งค่า", style=discord.ButtonStyle.primary)
    async def settings(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="🔗 ตั้งค่าระบบป้องกันลิงก์",
            description="เลือกเปิดหรือปิดระบบด้านล่างค่ะ...",
            color=discord.Color.blurple()
        )

        await interaction.response.edit_message(
            embed=embed,
            view=AntiLinkToggleView(self.guild_id)
        )


class AntiLink(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.warnings = {}

    # ===== Slash Command =====
    @app_commands.command(name="anti-link", description="ตั้งค่าระบบป้องกันลิงก์")
    async def anti_link(self, interaction: discord.Interaction):

        guild_id = interaction.guild.id

        if guild_id not in anti_link_status:
            anti_link_status[guild_id] = False

        embed = discord.Embed(
            title="🔗 ตั้งค่าระบบป้องกันลิงก์",
            description="กดปุ่มด้านล่างเพื่อจัดการระบบ",
            color=discord.Color.blurple()
        )

        embed.add_field(
            name="สถานะปัจจุบัน",
            value="📁 เปิดอยู่" if anti_link_status[guild_id] else "💢 ปิดอยู่",
            inline=False
        )

        await interaction.response.send_message(
            embed=embed,
            view=AntiLinkMainView(guild_id),
            ephemeral=True
        )

    # ===== ระบบตรวจลิงก์ =====
    @commands.Cog.listener()
    async def on_message(self, message):

        if message.author.bot or not message.guild:
            return

        guild_id = message.guild.id

        if not anti_link_status.get(guild_id, False):
            return

        # ตรวจลิงก์
        if re.search(r"https?://", message.content):

            try:
                await message.delete()
            except:
                pass

            key = (guild_id, message.author.id)
            self.warnings[key] = self.warnings.get(key, 0) + 1
            count = self.warnings[key]

            # เตือนครั้งที่ 1-2
            if count < 3:
                await message.channel.send(
                    f"💢 {message.author.mention} ห้ามส่งลิงก์ ({count}/3)",
                    delete_after=5
                )
                return

            # ครบ 3 ครั้ง แบน
            try:
                await message.author.ban(reason="ส่งลิงก์ครบ 3 ครั้ง")
                await message.channel.send(
                    f"🔨 {message.author.mention} ถูกแบน (ส่งลิงก์ครบ 3 ครั้ง)",
                    delete_after=5
                )
            except Exception as e:
                print("BAN ERROR:", e)

            self.warnings.pop(key, None)


async def setup(bot):
    await bot.add_cog(AntiLink(bot))