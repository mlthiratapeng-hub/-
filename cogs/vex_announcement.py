import discord
from discord.ext import commands
from discord import app_commands

CHANNEL_NAME = "📁ประกาศVEX·⌒ﾞ🍇"

class VEXAnnouncement(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # ==============================
    # 🔥 คำสั่ง !kong ส่งประกาศทุกเซิร์ฟ
    # ==============================
    @commands.command()
    async def kong(self, ctx, *, message):

        embed = discord.Embed(
            title="ประกาศจาก VEX",
            description=message,
            color=discord.Color.black()  # 🖤 ขอบสีดำ
        )

        embed.set_author(
            name=f"ประกาศจาก {ctx.author.display_name}",
            icon_url=ctx.author.display_avatar.url
        )

        embed.set_thumbnail(
            url=ctx.author.display_avatar.url
        )

        embed.timestamp = ctx.message.created_at
        embed.set_footer(text="VEX Announcement System")

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
    # 🔥 Slash สร้างห้องประกาศ
    # ==============================
    @app_commands.command(
        name="create_announcement_room",
        description="สร้างห้องประกาศ VEX"
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def create_announcement_room(self, interaction: discord.Interaction):

        guild = interaction.guild

        existing = discord.utils.get(guild.text_channels, name=CHANNEL_NAME)
        if existing:
            return await interaction.response.send_message(
                "มีห้องนี้อยู่แล้ว",
                ephemeral=True
            )

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(send_messages=False),
            guild.me: discord.PermissionOverwrite(send_messages=True)
        }

        channel = await guild.create_text_channel(
            CHANNEL_NAME,
            overwrites=overwrites
        )

        await interaction.response.send_message(
            f"📁 สร้างห้อง {channel.mention} เรียบร้อยแล้ว",
            ephemeral=True
        )


async def setup(bot):
    await bot.add_cog(VEXAnnouncement(bot))