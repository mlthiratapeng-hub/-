import discord
from discord.ext import commands
from discord import app_commands
import re

from cogs.whitelist import whitelist_data  # ดึง whitelist มาใช้

anti_link_mode = {}

class AntiLinkModeView(discord.ui.View):
    def __init__(self, guild_id):
        super().__init__(timeout=60)
        self.guild_id = guild_id

    async def update_embed(self, interaction, text, color):
        embed = discord.Embed(
            title="🔗 ระบบป้องกันลิงก์",
            description=text,
            color=color
        )
        await interaction.response.edit_message(embed=embed, view=None)

    @discord.ui.button(label="1️⃣ กันลิงก์เชิญดิส", style=discord.ButtonStyle.primary)
    async def invite_only(self, interaction: discord.Interaction, button: discord.ui.Button):
        anti_link_mode[self.guild_id] = 1
        await self.update_embed(interaction, "เปิดโหมด: กันเฉพาะลิงก์เชิญ Discord", discord.Color.blue())

    @discord.ui.button(label="2️⃣ กันลิงก์ภายนอก", style=discord.ButtonStyle.success)
    async def external_only(self, interaction: discord.Interaction, button: discord.ui.Button):
        anti_link_mode[self.guild_id] = 2
        await self.update_embed(interaction, "เปิดโหมด: กันลิงก์ภายนอก", discord.Color.green())

    @discord.ui.button(label="3️⃣ กันทุกลิงก์", style=discord.ButtonStyle.danger)
    async def all_links(self, interaction: discord.Interaction, button: discord.ui.Button):
        anti_link_mode[self.guild_id] = 3
        await self.update_embed(interaction, "เปิดโหมด: กันทุกลิงก์", discord.Color.red())

    @discord.ui.button(label="🍎 ปิดระบบ", style=discord.ButtonStyle.secondary)
    async def disable(self, interaction: discord.Interaction, button: discord.ui.Button):
        anti_link_mode[self.guild_id] = 0
        await self.update_embed(interaction, "ปิดระบบแล้ว", discord.Color.greyple())


class AntiLink(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.warnings = {}

    @app_commands.command(name="anti-link", description="ตั้งค่าระบบป้องกันลิงก์")
    async def anti_link(self, interaction: discord.Interaction):

        if not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message(
                "🍎 ใช้ได้เฉพาะแอดมิน",
                ephemeral=True
            )

        guild_id = interaction.guild.id
        anti_link_mode.setdefault(guild_id, 0)

        embed = discord.Embed(
            title="🔗 ตั้งค่าระบบป้องกันลิงก์",
            description="เลือกโหมดด้านล่าง",
            color=discord.Color.blurple()
        )

        await interaction.response.send_message(
            embed=embed,
            view=AntiLinkModeView(guild_id),
            ephemeral=True
        )

    @commands.Cog.listener()
    async def on_message(self, message):

        if message.author.bot or not message.guild:
            return

        guild_id = message.guild.id
        mode = anti_link_mode.get(guild_id, 0)

        # ✅ เช็ค whitelist ก่อน
        if message.author.id in whitelist_data.get(guild_id, set()):
            return

        if mode == 0:
            return

        content = message.content.lower()

        has_link = re.search(r"https?://", content)
        has_invite = re.search(r"(discord\.gg/|discord\.com/invite/)", content)

        violation = False

        if mode == 1 and has_invite:
            violation = True
        elif mode == 2 and has_link and not has_invite:
            violation = True
        elif mode == 3 and has_link:
            violation = True

        if not violation:
            return

        try:
            await message.delete()
        except:
            pass

        key = (guild_id, message.author.id)
        self.warnings[key] = self.warnings.get(key, 0) + 1
        count = self.warnings[key]

        if count < 3:
            await message.channel.send(
                f"💢 {message.author.mention} ห้ามส่งลิงก์ ({count}/3)",
                delete_after=5
            )
            return

        try:
            await message.author.ban(reason="ส่งลิงก์ครบ 3 ครั้ง")
            await message.channel.send(
                f"🔨 {message.author.mention} ถูกแบน (ครบ 3 ครั้ง)",
                delete_after=5
            )
        except Exception as e:
            print("BAN ERROR:", e)

        self.warnings.pop(key, None)


async def setup(bot):
    await bot.add_cog(AntiLink(bot))