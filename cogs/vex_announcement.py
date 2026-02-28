import discord
from discord.ext import commands
from discord import app_commands
import json
import os
from datetime import datetime

CHANNEL_NAME = "📁ประกาศVEX·⌒ﾞ🍇"
DATA_FILE = "announcement_data.json"
OWNER_ID = 1155481097753337916


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

    # ================================
    # 🔥 /สร้างห้อง
    # ================================
    @app_commands.command(name="สร้างห้อง")
    async def create_room(self, interaction: discord.Interaction):

        guild = interaction.guild

        if str(guild.id) in self.data:
            return await interaction.response.send_message(
                "มีห้องประกาศอยู่แล้ว",
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

        self.data[str(guild.id)] = channel.id
        save_data(self.data)

        await interaction.response.send_message(
            f"สร้างห้อง {channel.mention} เรียบร้อยแล้ว",
            ephemeral=True
        )

    # ================================
    # 🔥 !op
    # ================================
    @commands.command()
    async def op(self, ctx, *, message):

        if ctx.author.id != OWNER_ID:
            return

        embed = discord.Embed(
            title="🍇 VEX ANNOUNCEMENT",
            description=message,
            color=discord.Color.black()
        )

        embed.set_footer(
            text=f"VEX SYSTEM • {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}"
        )

        sent_count = 0

        for guild_id, channel_id in self.data.items():
            channel = self.bot.get_channel(channel_id)

            if channel:
                try:
                    await channel.send(embed=embed)
                    sent_count += 1
                except Exception as e:
                    print("Send Error:", e)

        await ctx.send(f"ส่งแล้ว {sent_count} เซิร์ฟเวอร์")

async def setup(bot):
    await bot.add_cog(VEXAnnouncement(bot))