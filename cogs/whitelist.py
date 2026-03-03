import discord
from discord.ext import commands
from discord import app_commands

# เก็บ whitelist แยกตาม guild
whitelist_data = {}

def is_whitelisted(guild_id: int, user_id: int):
    return user_id in whitelist_data.get(guild_id, set())


class WhitelistMainView(discord.ui.View):
    def __init__(self, guild_id):
        super().__init__(timeout=120)
        self.guild_id = guild_id

    @discord.ui.button(label="เพิ่ม", style=discord.ButtonStyle.secondary)
    async def add_user(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(
            content="เลือกผู้ใช้เพื่อเพิ่ม",
            view=WhitelistSelectView(self.guild_id, True)
        )

    @discord.ui.button(label="➖ ลบ", style=discord.ButtonStyle.secondary)
    async def remove_user(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(
            content="เลือกผู้ใช้เพื่อลบ",
            view=WhitelistSelectView(self.guild_id, False)
        )

    @discord.ui.button(label="📋 รายชื่อ", style=discord.ButtonStyle.secondary)
    async def list_users(self, interaction: discord.Interaction, button: discord.ui.Button):

        users = whitelist_data.get(self.guild_id, set())

        if not users:
            return await interaction.response.send_message("ไม่มี whitelist", ephemeral=True)

        embed = discord.Embed(
            title="📋 รายชื่อ Whitelist",
            description="\n".join(f"<@{u}>" for u in users),
            color=discord.Color.dark_gray()
        )

        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(label="🍓 ปิด", style=discord.ButtonStyle.secondary)
    async def close(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(content="ปิดเมนูแล้ว", view=None)


class WhitelistSelectView(discord.ui.View):
    def __init__(self, guild_id, add_mode):
        super().__init__(timeout=60)
        self.guild_id = guild_id
        self.add_mode = add_mode

        select = discord.ui.UserSelect(min_values=1, max_values=1)
        select.callback = self.callback
        self.add_item(select)

    async def callback(self, interaction: discord.Interaction):

        user_id = int(interaction.data["values"][0])
        whitelist_data.setdefault(self.guild_id, set())

        if self.add_mode:
            whitelist_data[self.guild_id].add(user_id)
            msg = f"🫛 เพิ่ม <@{user_id}> แล้ว"
        else:
            whitelist_data[self.guild_id].discard(user_id)
            msg = f"🍎 ลบ <@{user_id}> แล้ว"

        await interaction.response.edit_message(
            content=msg,
            view=WhitelistMainView(self.guild_id)
        )


class Whitelist(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="whitelist", description="จัดการ whitelist")
    async def whitelist(self, interaction: discord.Interaction):

        if not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message(
                "🥭 ใช้ได้เฉพาะแอดมิน",
                ephemeral=True
            )

        guild_id = interaction.guild.id
        whitelist_data.setdefault(guild_id, set())

        await interaction.response.send_message(
            "เมนู Whitelist",
            view=WhitelistMainView(guild_id),
            ephemeral=True
        )


async def setup(bot):
    await bot.add_cog(Whitelist(bot))