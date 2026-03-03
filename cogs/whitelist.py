import discord
from discord.ext import commands
from discord import app_commands
import json
import os

DATA_FILE = "whitelist_data.json"


class Whitelist(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.data = {}
        self.load_data()

    # =============================
    # DATA SYSTEM
    # =============================

    def load_data(self):
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                self.data = json.load(f)
        else:
            self.data = {}

    def save_data(self):
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(self.data, f, indent=4)

    def ensure_guild(self, guild_id):
        guild_id = str(guild_id)
        if guild_id not in self.data:
            self.data[guild_id] = {
                "users": {},
                "roles": {}
            }

    # =============================
    # CHECK BYPASS (เรียกใน Anti)
    # =============================

    def is_exempt(self, guild_id, member: discord.Member, module: str):
        guild_id = str(guild_id)
        if guild_id not in self.data:
            return False

        guild_data = self.data[guild_id]

        user_data = guild_data["users"].get(str(member.id))
        if user_data:
            if user_data.get("global_admin"):
                return True
            if user_data.get(module):
                return True

        for role in member.roles:
            role_data = guild_data["roles"].get(str(role.id))
            if role_data:
                if role_data.get("global_admin"):
                    return True
                if role_data.get(module):
                    return True

        return False

    # =============================
    # MAIN COMMAND
    # =============================

    @app_commands.command(name="whitelist", description="จัดการ Whitelist")
    async def whitelist(self, interaction: discord.Interaction):

        if not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message(
                "🥭 Admin เท่านั้น",
                ephemeral=True
            )

        self.ensure_guild(interaction.guild.id)

        embed = discord.Embed(
            title="🥕 ระบบจัดการ Whitelist",
            description="เลือกการทำงานด้านล่าง",
            color=discord.Color.purple()
        )

        await interaction.response.send_message(
            embed=embed,
            view=MainView(self),
            ephemeral=True
        )


# =============================
# MAIN VIEW
# =============================

class MainView(discord.ui.View):
    def __init__(self, cog):
        super().__init__(timeout=180)
        self.cog = cog

    @discord.ui.button(label="➕ เพิ่ม / แก้ไข", style=discord.ButtonStyle.green)
    async def manage(self, interaction, button):
        await interaction.response.edit_message(
            embed=discord.Embed(
                title="เลือกประเภท",
                description="เลือกว่าจะจัดการ ผู้ใช้ หรือ บทบาท",
                color=discord.Color.blurple()
            ),
            view=TypeView(self.cog)
        )

    @discord.ui.button(label="🗑 ลบออกจาก Whitelist", style=discord.ButtonStyle.red)
    async def delete(self, interaction, button):
        await interaction.response.edit_message(
            embed=discord.Embed(
                title="เลือกประเภทที่ต้องการลบ",
                color=discord.Color.red()
            ),
            view=DeleteTypeView(self.cog)
        )

    @discord.ui.button(label="📋 ดูรายชื่อ", style=discord.ButtonStyle.gray)
    async def view_list(self, interaction, button):

        guild_data = self.cog.data[str(interaction.guild.id)]

        users = "\n".join([f"<@{u}>" for u in guild_data["users"]]) or "ไม่มี"
        roles = "\n".join([f"<@&{r}>" for r in guild_data["roles"]]) or "ไม่มี"

        embed = discord.Embed(
            title="📋 รายชื่อ Whitelist",
            color=discord.Color.green()
        )
        embed.add_field(name="👤 Users", value=users, inline=False)
        embed.add_field(name="🛡 Roles", value=roles, inline=False)

        await interaction.response.edit_message(embed=embed, view=MainView(self.cog))


# =============================
# TYPE VIEW (ADD)
# =============================

class TypeView(discord.ui.View):
    def __init__(self, cog):
        super().__init__(timeout=180)
        self.cog = cog

    @discord.ui.button(label="ผู้ใช้", style=discord.ButtonStyle.primary)
    async def user_btn(self, interaction, button):
        await interaction.response.edit_message(
            embed=discord.Embed(title="เลือกผู้ใช้"),
            view=UserSelectView(self.cog)
        )

    @discord.ui.button(label="บทบาท", style=discord.ButtonStyle.primary)
    async def role_btn(self, interaction, button):
        await interaction.response.edit_message(
            embed=discord.Embed(title="เลือกบทบาท"),
            view=RoleSelectView(self.cog)
        )


# =============================
# DELETE TYPE VIEW
# =============================

class DeleteTypeView(discord.ui.View):
    def __init__(self, cog):
        super().__init__(timeout=180)
        self.cog = cog

    @discord.ui.button(label="ลบผู้ใช้", style=discord.ButtonStyle.red)
    async def del_user(self, interaction, button):
        await interaction.response.edit_message(
            embed=discord.Embed(title="เลือกผู้ใช้ที่จะลบ"),
            view=DeleteUserView(self.cog)
        )

    @discord.ui.button(label="ลบบทบาท", style=discord.ButtonStyle.red)
    async def del_role(self, interaction, button):
        await interaction.response.edit_message(
            embed=discord.Embed(title="เลือกบทบาทที่จะลบ"),
            view=DeleteRoleView(self.cog)
        )


# =============================
# USER SELECT (ADD)
# =============================

class UserSelectView(discord.ui.View):
    def __init__(self, cog):
        super().__init__(timeout=180)
        self.cog = cog
        self.add_item(discord.ui.UserSelect(min_values=1, max_values=1))

    async def interaction_check(self, interaction):
        user_id = interaction.data["values"][0]
        await interaction.response.edit_message(
            embed=discord.Embed(
                title="กำหนดสิทธิ์",
                description=f"ตั้งค่าให้ <@{user_id}>"
            ),
            view=PermissionView(self.cog, "users", user_id)
        )
        return False


class RoleSelectView(discord.ui.View):
    def __init__(self, cog):
        super().__init__(timeout=180)
        self.cog = cog
        self.add_item(discord.ui.RoleSelect(min_values=1, max_values=1))

    async def interaction_check(self, interaction):
        role_id = interaction.data["values"][0]
        await interaction.response.edit_message(
            embed=discord.Embed(
                title="กำหนดสิทธิ์",
                description=f"ตั้งค่าให้ <@&{role_id}>"
            ),
            view=PermissionView(self.cog, "roles", role_id)
        )
        return False


# =============================
# DELETE SELECT
# =============================

class DeleteUserView(discord.ui.View):
    def __init__(self, cog):
        super().__init__(timeout=180)
        self.cog = cog
        self.add_item(discord.ui.UserSelect(min_values=1, max_values=1))

    async def interaction_check(self, interaction):
        user_id = interaction.data["values"][0]
        guild_id = str(interaction.guild.id)

        if user_id in self.cog.data[guild_id]["users"]:
            del self.cog.data[guild_id]["users"][user_id]
            self.cog.save_data()
            msg = "🍈 ลบผู้ใช้แล้ว"
        else:
            msg = "🍒 ผู้ใช้นี้ไม่ได้อยู่ใน Whitelist"

        await interaction.response.edit_message(
            embed=discord.Embed(description=msg),
            view=None
        )
        return False


class DeleteRoleView(discord.ui.View):
    def __init__(self, cog):
        super().__init__(timeout=180)
        self.cog = cog
        self.add_item(discord.ui.RoleSelect(min_values=1, max_values=1))

    async def interaction_check(self, interaction):
        role_id = interaction.data["values"][0]
        guild_id = str(interaction.guild.id)

        if role_id in self.cog.data[guild_id]["roles"]:
            del self.cog.data[guild_id]["roles"][role_id]
            self.cog.save_data()
            msg = "🌽 ลบบทบาทแล้ว"
        else:
            msg = "🍓 บทบาทนี้ไม่ได้อยู่ใน Whitelist"

        await interaction.response.edit_message(
            embed=discord.Embed(description=msg),
            view=None
        )
        return False


# =============================
# PERMISSION VIEW
# =============================

class PermissionView(discord.ui.View):
    def __init__(self, cog, target_type, target_id):
        super().__init__(timeout=180)
        self.cog = cog
        self.target_type = target_type
        self.target_id = target_id
        self.selected = {
            "anti_link": False,
            "anti_spam": False,
            "anti_nuke": False,
            "global_admin": False
        }

    @discord.ui.select(
        placeholder="เลือกสิทธิ์",
        min_values=1,
        max_values=4,
        options=[
            discord.SelectOption(label="Global Admin", value="global_admin"),
            discord.SelectOption(label="Anti-Link", value="anti_link"),
            discord.SelectOption(label="Anti-Spam", value="anti_spam"),
            discord.SelectOption(label="Anti-Nuke", value="anti_nuke"),
        ]
    )
    async def select_callback(self, interaction, select):
        for value in select.values:
            self.selected[value] = True
        await interaction.response.defer()

    @discord.ui.button(label="บันทึก", style=discord.ButtonStyle.green)
    async def save_btn(self, interaction, button):

        guild_id = str(interaction.guild.id)
        self.cog.ensure_guild(guild_id)

        self.cog.data[guild_id][self.target_type][self.target_id] = self.selected
        self.cog.save_data()

        await interaction.response.edit_message(
            embed=discord.Embed(description="🌮 บันทึกสำเร็จ"),
            view=None
        )


async def setup(bot):
    await bot.add_cog(Whitelist(bot))