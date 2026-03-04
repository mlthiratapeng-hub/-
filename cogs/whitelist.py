import discord
from discord import app_commands
from discord.ext import commands
from typing import Optional

from prevent import whitelist_data

# =========================
# PERMISSION TYPES
# =========================

PERMISSION_TYPES = [
    ("GLOBAL", "🌍 Global Admin"),
    ("ANTI_NUKE", "💣 Anti-Nuke"),
    ("ANTI_SPAM", "📁 Anti-Spam"),
    ("ANTI_LINK", "🔗 Anti-Link"),
    ("TRUSTED", "⭐ Trusted")
]

# =========================
# SELECT PERMISSION VIEW
# =========================

class PermissionSelect(discord.ui.Select):
    def __init__(self, guild_id: int, target_id: int):

        self.guild_id = guild_id
        self.target_id = target_id

        options = [
            discord.SelectOption(label=name, value=value)
            for value, name in PERMISSION_TYPES
        ]

        super().__init__(
            placeholder="เลือกสิทธิ์ที่ต้องการให้...",
            min_values=1,
            max_values=len(options),
            options=options
        )

    async def callback(self, interaction: discord.Interaction):

        if self.guild_id not in whitelist_data:
            whitelist_data[self.guild_id] = {}

        whitelist_data[self.guild_id][self.target_id] = self.values

        embed = discord.Embed(
            title="✅ บันทึกสำเร็จ",
            description="เพิ่มสิทธิ์ให้เป้าหมายเรียบร้อยแล้ว",
            color=discord.Color.green()
        )

        await interaction.response.edit_message(embed=embed, view=None)


class PermissionView(discord.ui.View):
    def __init__(self, guild_id: int, target_id: int):
        super().__init__(timeout=60)
        self.add_item(PermissionSelect(guild_id, target_id))


# =========================
# LIST VIEW (Pagination)
# =========================

class WhitelistListView(discord.ui.View):
    def __init__(self, guild_id: int):
        super().__init__(timeout=60)
        self.guild_id = guild_id
        self.page = 0

    def generate_embed(self):
        embed = discord.Embed(
            title="📋 รายการ Whitelist",
            color=discord.Color.blurple()
        )

        data = whitelist_data.get(self.guild_id, {})
        items = list(data.items())

        if not items:
            embed.description = "ยังไม่มีข้อมูล"
            return embed

        per_page = 5
        start = self.page * per_page
        end = start + per_page

        for target_id, perms in items[start:end]:
            embed.add_field(
                name=f"ID: {target_id}",
                value=", ".join(perms),
                inline=False
            )

        embed.set_footer(text=f"หน้า {self.page + 1}")

        return embed

    @discord.ui.button(label="◀", style=discord.ButtonStyle.secondary)
    async def previous(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.page > 0:
            self.page -= 1
        await interaction.response.edit_message(embed=self.generate_embed(), view=self)

    @discord.ui.button(label="▶", style=discord.ButtonStyle.secondary)
    async def next(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.page += 1
        await interaction.response.edit_message(embed=self.generate_embed(), view=self)


# =========================
# COG
# =========================

class Whitelist(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="whitelist_add", description="เพิ่มเป้าหมายเข้า whitelist")
    async def whitelist_add(
        self,
        interaction: discord.Interaction,
        user: Optional[discord.Member] = None,
        role: Optional[discord.Role] = None,
        channel: Optional[discord.TextChannel] = None
    ):

        if not interaction.guild:
            return

        if not any([user, role, channel]):
            await interaction.response.send_message(
                "ต้องเลือกอย่างใดอย่างหนึ่ง (user/role/channel)",
                ephemeral=True
            )
            return

        target = user or role or channel
        target_id = target.id

        embed = discord.Embed(
            title="⚙ เลือกสิทธิ์",
            description=f"กำหนดสิทธิ์ให้ `{target}`",
            color=discord.Color.orange()
        )

        await interaction.response.send_message(
            embed=embed,
            view=PermissionView(interaction.guild.id, target_id),
            ephemeral=True
        )

    @app_commands.command(name="whitelist_remove", description="ลบออกจาก whitelist")
    async def whitelist_remove(
        self,
        interaction: discord.Interaction,
        target_id: str
    ):

        guild_id = interaction.guild.id

        if guild_id in whitelist_data and int(target_id) in whitelist_data[guild_id]:
            del whitelist_data[guild_id][int(target_id)]

            await interaction.response.send_message(
                "ลบสำเร็จแล้ว",
                ephemeral=True
            )
        else:
            await interaction.response.send_message(
                "ไม่พบข้อมูล",
                ephemeral=True
            )

    @app_commands.command(name="whitelist_list", description="ดูรายการ whitelist")
    async def whitelist_list(self, interaction: discord.Interaction):

        view = WhitelistListView(interaction.guild.id)

        await interaction.response.send_message(
            embed=view.generate_embed(),
            view=view,
            ephemeral=True
        )


# =========================
# SETUP
# =========================

async def setup(bot):
    await bot.add_cog(Whitelist(bot))