import discord
from discord.ext import commands
from discord import app_commands

whitelist_data = {}


def ensure_guild(guild_id: int):
    whitelist_data.setdefault(guild_id, {"users": {}, "roles": {}})


def check_bypass(guild_id: int, member: discord.Member, system: str):
    ensure_guild(guild_id)

    # เช็ค user
    user_data = whitelist_data[guild_id]["users"].get(member.id)
    if user_data and user_data.get(system):
        return True

    # เช็ค role
    for role in member.roles:
        role_data = whitelist_data[guild_id]["roles"].get(role.id)
        if role_data and role_data.get(system):
            return True

    return False


# ================= VIEW =================

class MainView(discord.ui.View):
    def __init__(self, guild_id):
        super().__init__(timeout=120)
        self.guild_id = guild_id

    @discord.ui.button(label="⚙ จัดการ Whitelist", style=discord.ButtonStyle.secondary)
    async def manage(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(
            embed=discord.Embed(
                title="⚙ เลือกประเภท",
                description="เลือกว่าจะจัดการผู้ใช้หรือยศ",
                color=discord.Color.dark_gray()
            ),
            view=TypeSelectView(self.guild_id)
        )

    @discord.ui.button(label="📋 ดูรายการ", style=discord.ButtonStyle.secondary)
    async def view_list(self, interaction: discord.Interaction, button: discord.ui.Button):
        ensure_guild(self.guild_id)
        data = whitelist_data[self.guild_id]

        desc = ""

        for uid in data["users"]:
            desc += f"👤 <@{uid}>\n"

        for rid in data["roles"]:
            desc += f"🛡 <@&{rid}>\n"

        if not desc:
            desc = "ไม่มีข้อมูล"

        embed = discord.Embed(
            title="📋 รายชื่อ Whitelist",
            description=desc,
            color=discord.Color.dark_gray()
        )

        await interaction.response.edit_message(embed=embed, view=self)


class TypeSelectView(discord.ui.View):
    def __init__(self, guild_id):
        super().__init__(timeout=60)
        self.guild_id = guild_id

    @discord.ui.button(label="👤 ผู้ใช้", style=discord.ButtonStyle.secondary)
    async def user_select(self, interaction: discord.Interaction, button: discord.ui.Button):
        view = TargetSelectView(self.guild_id, "users")
        await interaction.response.edit_message(view=view)

    @discord.ui.button(label="🛡 ยศ", style=discord.ButtonStyle.secondary)
    async def role_select(self, interaction: discord.Interaction, button: discord.ui.Button):
        view = TargetSelectView(self.guild_id, "roles")
        await interaction.response.edit_message(view=view)


class TargetSelectView(discord.ui.View):
    def __init__(self, guild_id, mode):
        super().__init__(timeout=60)
        self.guild_id = guild_id
        self.mode = mode

        if mode == "users":
            select = discord.ui.UserSelect(min_values=1, max_values=1)
        else:
            select = discord.ui.RoleSelect(min_values=1, max_values=1)

        select.callback = self.callback
        self.add_item(select)

    async def callback(self, interaction: discord.Interaction):
        target_id = int(interaction.data["values"][0])
        ensure_guild(self.guild_id)

        view = PermissionSelectView(self.guild_id, self.mode, target_id)

        if self.mode == "users":
            member = interaction.guild.get_member(target_id)
            embed = discord.Embed(
                title="👤 โปรไฟล์ผู้ใช้",
                description=member.mention,
                color=discord.Color.dark_gray()
            )
            embed.set_thumbnail(url=member.display_avatar.url)
        else:
            role = interaction.guild.get_role(target_id)
            embed = discord.Embed(
                title="🛡 ข้อมูลยศ",
                description=role.mention,
                color=discord.Color.dark_gray()
            )

        await interaction.response.edit_message(embed=embed, view=view)


class PermissionSelectView(discord.ui.View):
    def __init__(self, guild_id, mode, target_id):
        super().__init__(timeout=120)
        self.guild_id = guild_id
        self.mode = mode
        self.target_id = target_id

    @discord.ui.button(label="🔗 Anti-Link", style=discord.ButtonStyle.secondary)
    async def anti_link(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.toggle("anti_link")
        await interaction.response.defer()

    @discord.ui.button(label="🛡 Anti-Spam", style=discord.ButtonStyle.secondary)
    async def anti_spam(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.toggle("anti_spam")
        await interaction.response.defer()

    @discord.ui.button(label="💣 Anti-Nuke", style=discord.ButtonStyle.secondary)
    async def anti_nuke(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.toggle("anti_nuke")
        await interaction.response.defer()

    @discord.ui.button(label="📂 บันทึก", style=discord.ButtonStyle.success)
    async def save(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(content="บันทึกเรียบร้อย", view=None)

    @discord.ui.button(label="🗑 ลบข้อมูล", style=discord.ButtonStyle.danger)
    async def delete(self, interaction: discord.Interaction, button: discord.ui.Button):
        ensure_guild(self.guild_id)
        whitelist_data[self.guild_id][self.mode].pop(self.target_id, None)
        await interaction.response.edit_message(content="ลบข้อมูลเรียบร้อย", view=None)

    def toggle(self, system):
        ensure_guild(self.guild_id)
        target_dict = whitelist_data[self.guild_id][self.mode]
        target_dict.setdefault(self.target_id, {
            "anti_link": False,
            "anti_spam": False,
            "anti_nuke": False
        })
        target_dict[self.target_id][system] = not target_dict[self.target_id][system]


class Whitelist(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="whitelist", description="จัดการระบบ whitelist")
    async def whitelist(self, interaction: discord.Interaction):

        if not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message(
                "🍅 ใช้ได้เฉพาะแอดมิน",
                ephemeral=True
            )

        ensure_guild(interaction.guild.id)

        embed = discord.Embed(
            title="📁 ระบบจัดการ Whitelist",
            description="กดปุ่มด้านล่างเพื่อจัดการ",
            color=discord.Color.dark_gray()
        )

        await interaction.response.send_message(
            embed=embed,
            view=MainView(interaction.guild.id),
            ephemeral=True
        )


async def setup(bot):
    await bot.add_cog(Whitelist(bot))