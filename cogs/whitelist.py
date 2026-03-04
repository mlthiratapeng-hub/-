import discord
from discord import app_commands
from discord.ext import commands
from typing import Optional

# =========================
# GLOBAL STORAGE
# =========================

whitelist_data = {}

def is_whitelisted(guild_id: int, target_id: int, module: str):
    if guild_id not in whitelist_data:
        return False

    data = whitelist_data[guild_id]

    if target_id not in data:
        return False

    perms = data[target_id]

    if "GLOBAL" in perms:
        return True

    return module in perms


# =========================
# PERMISSIONS
# =========================

PERMISSION_TYPES = [
    ("GLOBAL", "🌍 Global Admin"),
    ("ANTI_NUKE", "💣 Anti-Nuke"),
    ("ANTI_SPAM", "📁 Anti-Spam"),
    ("ANTI_LINK", "🔗 Anti-Link"),
    ("TRUSTED", "⭐ Trusted")
]


# =========================
# SELECT VIEW
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
            placeholder="เลือกสิทธิ์...",
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
            color=discord.Color.green()
        )

        await interaction.response.edit_message(embed=embed, view=None)


class PermissionView(discord.ui.View):
    def __init__(self, guild_id: int, target_id: int):
        super().__init__(timeout=60)
        self.add_item(PermissionSelect(guild_id, target_id))


# =========================
# COG
# =========================

class Whitelist(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="whitelist_add")
    async def whitelist_add(
        self,
        interaction: discord.Interaction,
        user: Optional[discord.Member] = None,
        role: Optional[discord.Role] = None,
        channel: Optional[discord.TextChannel] = None
    ):

        if not interaction.guild:
            return

        target = user or role or channel

        if not target:
            await interaction.response.send_message(
                "ต้องเลือก user/role/channel",
                ephemeral=True
            )
            return

        embed = discord.Embed(
            title="⚙ เลือกสิทธิ์",
            description=f"กำหนดสิทธิ์ให้ {target}",
            color=discord.Color.orange()
        )

        await interaction.response.send_message(
            embed=embed,
            view=PermissionView(interaction.guild.id, target.id),
            ephemeral=True
        )


async def setup(bot):
    await bot.add_cog(Whitelist(bot))