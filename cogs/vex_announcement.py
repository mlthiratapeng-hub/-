import discord
from discord import app_commands
from discord.ext import commands

CHANNEL_NAME = "📁ประกาศVEX·⌒ﾞ🍇"

class VEXAnnouncement(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # ==============================
    # สร้างห้องประกาศ
    # ==============================
    @app_commands.command(
        name="create_announcement_room",
        description="สร้างห้องประกาศข่าวVEX"
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def create_announcement_room(self, interaction: discord.Interaction):

        guild = interaction.guild

        # เช็คว่ามีอยู่แล้วไหม
        existing = discord.utils.get(guild.text_channels, name=CHANNEL_NAME)
        if existing:
            await interaction.response.send_message(
                "🍲 มีห้องประกาศVEX อยู่แล้ว",
                ephemeral=True
            )
            return

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(send_messages=False),
            guild.me: discord.PermissionOverwrite(send_messages=True)
        }

        channel = await guild.create_text_channel(
            CHANNEL_NAME,
            overwrites=overwrites
        )

        await interaction.response.send_message(
            f"🍇 สร้างห้อง {channel.mention} เรียบร้อยแล้ว💢",
            ephemeral=True
        )

    # ==============================
    # !kong ส่งประกาศทุกเซิร์ฟ
    # ==============================
    @commands.command()
    @commands.is_owner()
    async def kong(self, ctx, *, message):

        embed = discord.Embed(
            title="📁 ประกาศจาก VEX·⌒ﾞ🍇",
            description=message,
            color=discord.Color.purple()
        )
        embed.set_footer(text="VEX Global Announcement")

        sent_count = 0

        for guild in self.bot.guilds:
            channel = discord.utils.get(guild.text_channels, name=CHANNEL_NAME)
            if channel:
                try:
                    await channel.send(embed=embed)
                    sent_count += 1
                except:
                    pass

        await ctx.send(f"🍃 ส่งประกาศแล้ว {sent_count} เซิร์ฟเวอร์")

# ==============================
# Setup
# ==============================
async def setup(bot):
    await bot.add_cog(VEXAnnouncement(bot))