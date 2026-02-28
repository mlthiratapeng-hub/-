import discord
from discord.ext import commands
from discord import app_commands
import json
import os

CHANNEL_NAME = "📁ประกาศVEX·⌒ﾞ🍇"
DATA_FILE = "announcement_channels.json"


def load_data():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)


class VEXAnnouncement(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.data = load_data()

    # =====================================
    # 🔥 !kong ส่งประกาศทุกเซิร์ฟตาม ID
    # =====================================
    @commands.command()
    async def kong(self, ctx, *, message):

        embed = discord.Embed(
            title="ประกาศจาก VEX",
            description=message,
            color=discord.Color.black()
        )
        embed.set_author(
            name=f"ประกาศจาก {ctx.author.display_name}",
            icon_url=ctx.author.display_avatar.url
        )
        embed.timestamp = ctx.message.created_at
        embed.set_footer(text="VEX Announcement System")

        sent_count = 0

        for guild_id, channel_id in self.data.items():
            channel = self.bot.get_channel(channel_id)
            if channel:
                try:
                    await channel.send(embed=embed)
                    sent_count += 1
                except:
                    pass

        await ctx.send(f"📢 ส่งประกาศแล้ว {sent_count} เซิร์ฟเวอร์")

    # =====================================
    # 🔥 /create_announcement_room
    # =====================================
    @app_commands.command(
        name="create_announcement_room",
        description="สร้างห้องประกาศ VEX"
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def create_announcement_room(self, interaction: discord.Interaction):

        guild = interaction.guild

        # เช็คว่ามีบันทึกไว้แล้วไหม
        if str(guild.id) in self.data:
            return await interaction.response.send_message(
                "เซิร์ฟนี้มีห้องประกาศอยู่แล้ว",
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

        # บันทึก ID ห้อง
        self.data[str(guild.id)] = channel.id
        save_data(self.data)

        await interaction.response.send_message(
            f"🍃 สร้างห้อง {channel.mention} เรียบร้อยแล้ว",
            ephemeral=True
        )


async def setup(bot):
    await bot.add_cog(VEXAnnouncement(bot))