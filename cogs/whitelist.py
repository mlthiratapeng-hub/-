import discord
from discord.ext import commands
from discord import app_commands
import json
import os
import re

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
            self.data[guild_id] = {"users": {}, "roles": {}}

    # =============================
    # CHECK BYPASS (ANTI SYSTEM)
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
    # ANTI LINK (ตัวอย่าง)
    # =============================

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if not message.guild or message.author.bot:
            return

        if re.search(r"https?://", message.content):
            if self.is_exempt(message.guild.id, message.author, "anti_link"):
                return

            await message.delete()
            await message.channel.send(
                f"🚫 {message.author.mention} ห้ามส่งลิงก์!",
                delete_after=5
            )

    # =============================
    # SLASH COMMAND
    # =============================

    @app_commands.command(name="whitelist", description="📁 จัดการ Whitelist")
    async def whitelist(self, interaction: discord.Interaction):

        if not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message(
                "🍒 Admin เท่านั้น",
                ephemeral=True
            )

        self.ensure_guild(interaction.guild.id)

        await interaction.response.send_message(
            embed=main_embed(),
            view=MainView(self),
            ephemeral=True
        )


# =============================
# EMBEDS
# =============================

def main_embed():
    return discord.Embed(
        title="📁 ระบบ Whitelist",
        description="เลือกเมนูด้านล่าง",
        color=discord.Color.purple()
    )


def format_permissions(data: dict):
    perms = []
    if data.get("global_admin"):
        perms.append("📂 Global")
    if data.get("anti_link"):
        perms.append("🔗 Anti-Link")
    if data.get("anti_spam"):
        perms.append("💬 Anti-Spam")
    if data.get("anti_nuke"):
        perms.append("💣 Anti-Nuke")
    return ", ".join(perms) if perms else "ไม่มีสิทธิ์"


# =============================
# MAIN VIEW
# =============================

class MainView(discord.ui.View):
    def __init__(self, cog):
        super().__init__(timeout=180)
        self.cog = cog

    @discord.ui.button(label="เพิ่ม / แก้ไข", emoji="🌶️", style=discord.ButtonStyle.green)
    async def manage(self, interaction, button):
        await interaction.response.edit_message(
            embed=discord.Embed(title="🛠 เลือกประเภท"),
            view=TypeView(self.cog)
        )

    @discord.ui.button(label="ดูรายการ", emoji="🗃️", style=discord.ButtonStyle.primary)
    async def view_list(self, interaction, button):
        await interaction.response.edit_message(
            embed=build_list_embed(self.cog, interaction.guild),
            view=ListView(self.cog)
        )

    @discord.ui.button(label="ปิด", emoji="❌", style=discord.ButtonStyle.gray)
    async def close(self, interaction, button):
        await interaction.message.delete()


# =============================
# LIST VIEW
# =============================

def build_list_embed(cog, guild):
    cog.ensure_guild(guild.id)
    data = cog.data[str(guild.id)]

    embed = discord.Embed(
        title="🗃️ รายชื่อที่ถูก Whitelist",
        color=discord.Color.blue()
    )

    user_text = ""
    for uid, info in data["users"].items():
        member = guild.get_member(int(uid))
        name = member.name if member else f"User {uid}"
        user_text += f"👤 {name} → {format_permissions(info)}\n"

    role_text = ""
    for rid, info in data["roles"].items():
        role = guild.get_role(int(rid))
        name = role.name if role else f"Role {rid}"
        role_text += f"🛡 {name} → {format_permissions(info)}\n"

    embed.add_field(name="👤 ผู้ใช้", value=user_text or "ไม่มี", inline=False)
    embed.add_field(name="🛡 บทบาท", value=role_text or "ไม่มี", inline=False)

    return embed


class ListView(discord.ui.View):
    def __init__(self, cog):
        super().__init__(timeout=180)
        self.cog = cog

    @discord.ui.button(label="ลบออกจาก Whitelist", emoji="🗑", style=discord.ButtonStyle.danger)
    async def remove_btn(self, interaction, button):
        await interaction.response.edit_message(
            embed=discord.Embed(title="🗑 เลือกประเภทที่ต้องการลบ"),
            view=RemoveTypeView(self.cog)
        )

    @discord.ui.button(label="ย้อนกลับ", emoji="🔙", style=discord.ButtonStyle.secondary)
    async def back(self, interaction, button):
        await interaction.response.edit_message(
            embed=main_embed(),
            view=MainView(self.cog)
        )


# =============================
# REMOVE SYSTEM
# =============================

class RemoveTypeView(discord.ui.View):
    def __init__(self, cog):
        super().__init__(timeout=180)
        self.cog = cog

    @discord.ui.button(label="ลบผู้ใช้", emoji="👤", style=discord.ButtonStyle.primary)
    async def remove_user(self, interaction, button):
        await interaction.response.edit_message(
            embed=discord.Embed(title="👤 เลือกผู้ใช้ที่ถูก Whitelist"),
            view=RemoveUserSelect(self.cog)
        )

    @discord.ui.button(label="ลบบทบาท", emoji="🛡", style=discord.ButtonStyle.primary)
    async def remove_role(self, interaction, button):
        await interaction.response.edit_message(
            embed=discord.Embed(title="🛡 เลือกบทบาทที่ถูก Whitelist"),
            view=RemoveRoleSelect(self.cog)
        )


class RemoveUserSelect(discord.ui.View):
    def __init__(self, cog):
        super().__init__(timeout=180)
        self.cog = cog

        options = []
        data = cog.data.get
        # dynamic later in interaction

    async def interaction_check(self, interaction):
        return True


class RemoveRoleSelect(discord.ui.View):
    def __init__(self, cog):
        super().__init__(timeout=180)
        self.cog = cog


# =============================
# TYPE VIEW (ADD)
# =============================

class TypeView(discord.ui.View):
    def __init__(self, cog):
        super().__init__(timeout=180)
        self.cog = cog

    @discord.ui.button(label="ผู้ใช้", emoji="👤", style=discord.ButtonStyle.primary)
    async def user_btn(self, interaction, button):
        await interaction.response.edit_message(
            embed=discord.Embed(title="👤 เลือกผู้ใช้"),
            view=UserSelectView(self.cog)
        )

    @discord.ui.button(label="บทบาท", emoji="🛡", style=discord.ButtonStyle.primary)
    async def role_btn(self, interaction, button):
        await interaction.response.edit_message(
            embed=discord.Embed(title="🛡 เลือกบทบาท"),
            view=RoleSelectView(self.cog)
        )

    @discord.ui.button(label="ย้อนกลับ", emoji="🔙", style=discord.ButtonStyle.secondary)
    async def back(self, interaction, button):
        await interaction.response.edit_message(
            embed=main_embed(),
            view=MainView(self.cog)
        )


# =============================
# ADD SYSTEM
# =============================

class UserSelectView(discord.ui.View):
    def __init__(self, cog):
        super().__init__(timeout=180)
        self.cog = cog
        self.add_item(discord.ui.UserSelect(min_values=1, max_values=1))

    async def interaction_check(self, interaction):
        user_id = int(interaction.data["values"][0])
        await interaction.response.edit_message(
            embed=discord.Embed(title="🔐 เลือกสิทธิ์"),
            view=PermissionView(self.cog, "users", str(user_id))
        )
        return False


class RoleSelectView(discord.ui.View):
    def __init__(self, cog):
        super().__init__(timeout=180)
        self.cog = cog
        self.add_item(discord.ui.RoleSelect(min_values=1, max_values=1))

    async def interaction_check(self, interaction):
        role_id = int(interaction.data["values"][0])
        await interaction.response.edit_message(
            embed=discord.Embed(title="🔐 เลือกสิทธิ์"),
            view=PermissionView(self.cog, "roles", str(role_id))
        )
        return False


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
        placeholder="🔐 เลือกสิทธิ์",
        min_values=1,
        max_values=4,
        options=[
            discord.SelectOption(label="📂 Global Admin", value="global_admin"),
            discord.SelectOption(label="🔗 Anti-Link", value="anti_link"),
            discord.SelectOption(label="💬 Anti-Spam", value="anti_spam"),
            discord.SelectOption(label="💣 Anti-Nuke", value="anti_nuke"),
        ]
    )
    async def select_callback(self, interaction, select):
        for value in select.values:
            self.selected[value] = True
        await interaction.response.defer()

    @discord.ui.button(label="บันทึก", emoji="📁", style=discord.ButtonStyle.green)
    async def save_btn(self, interaction, button):
        guild_id = str(interaction.guild.id)
        self.cog.ensure_guild(guild_id)
        self.cog.data[guild_id][self.target_type][self.target_id] = self.selected
        self.cog.save_data()

        await interaction.response.edit_message(
            embed=discord.Embed(description="🍇 บันทึกเรียบร้อย"),
            view=MainView(self.cog)
        )


async def setup(bot):
    await bot.add_cog(Whitelist(bot))