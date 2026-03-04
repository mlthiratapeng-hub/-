import discord
from discord import app_commands
from discord.ext import commands
from prevent import is_prevent_enabled  # 👈 เชื่อมระบบ prevent

anti_spam_status = {}

# ================= TOGGLE VIEW =================

class AntiSpamToggleView(discord.ui.View):
    def __init__(self, guild_id: int):
        super().__init__(timeout=60)
        self.guild_id = guild_id

    @discord.ui.button(label="เปิดระบบ", style=discord.ButtonStyle.success, emoji="📁")
    async def enable(self, interaction: discord.Interaction, button: discord.ui.Button):

        # ❌ ถ้า prevent ปิด ไม่ให้เปิด
        if not is_prevent_enabled(self.guild_id):
            embed = discord.Embed(
                title="🛡️ ระบบป้องกันสแปม",
                description="❌ ไม่สามารถเปิดได้ เพราะ Prevent ยังปิดอยู่",
                color=discord.Color.red()
            )
            await interaction.response.edit_message(embed=embed, view=None)
            return

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
            name="สถานะ Anti-Spam",
            value="📁 เปิดอยู่" if anti_spam_status[guild_id] else "💢 ปิดอยู่",
            inline=False
        )

        # 👇 เพิ่มสถานะ Prevent
        embed.add_field(
            name="สถานะ Prevent",
            value="🛡️ เปิดอยู่" if is_prevent_enabled(guild_id) else "❌ ปิดอยู่",
            inline=False
        )

        await interaction.response.send_message(
            embed=embed,
            view=AntiSpamMainView(guild_id),
            ephemeral=True
        )


# ================= SETUP =================

async def setup(bot):
    await bot.add_cog(AntiSpam(bot))