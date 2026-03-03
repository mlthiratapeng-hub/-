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

    # ================= DATA =================

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

    # ================= CHECK =================

    def is_exempt(self, guild_id, member: discord.Member, module: str):
        guild_id = str(guild_id)
        if guild_id not in self.data:
            return False

        guild_data = self.data[guild_id]

        user_data = guild_data["users"].get(str(member.id))
        if user_data:
            if user_data.get("global_admin") or user_data.get(module):
                return True

        for role in member.roles:
            role_data = guild_data["roles"].get(str(role.id))
            if role_data:
                if role_data.get("global_admin") or role_data.get(module):
                    return True

        return False

    # ================= ANTI LINK =================

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

    # ================= SLASH =================

    @app_commands.command(name="whitelist", description="จัดการ Whitelist")
    async def whitelist(self, interaction: discord.Interaction):

        if not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message(
                "❌ Admin เท่านั้น",
                ephemeral=True
            )

        self.ensure_guild(interaction.guild.id)

        await interaction.response.send_message(
            embed=main_embed(),
            view=MainView(self),
            ephemeral=True
        )


# ================= EMBEDS =================

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
    return "\n".join(perms) if perms else "ไม่มีสิทธิ์"


# ================= MAIN VIEW =================

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

    @discord.ui.button(label="📋 ดูรายการ", emoji="📋", style=discord.ButtonStyle.primary)
    async def view_list(self, interaction, button):
        await interaction.response.edit_message(
            embed=discord.Embed(title="📋 เลือกประเภท"),
            view=ViewType(self.cog)
        )

    @discord.ui.button(label="ปิด", emoji="❌", style=discord.ButtonStyle.gray)
    async def close(self, interaction, button):
        await interaction.message.delete()


# ================= VIEW TYPE =================

class ViewType(discord.ui.View):
    def __init__(self, cog):
        super().__init__(timeout=180)
        self.cog = cog

    @discord.ui.button(label="ผู้ใช้", emoji="👤", style=discord.ButtonStyle.primary)
    async def view_users(self, interaction, button):
        await interaction.response.edit_message(
            embed=discord.Embed(title="👤 เลือกผู้ใช้ที่ถูก Whitelist"),
            view=UserListView(self.cog)
        )

    @discord.ui.button(label="บทบาท", emoji="🛡", style=discord.ButtonStyle.primary)
    async def view_roles(self, interaction, button):
        await interaction.response.edit_message(
            embed=discord.Embed(title="🛡 เลือกบทบาทที่ถูก Whitelist"),
            view=RoleListView(self.cog)
        )

    @discord.ui.button(label="ย้อนกลับ", emoji="🔙", style=discord.ButtonStyle.secondary)
    async def back(self, interaction, button):
        await interaction.response.edit_message(
            embed=main_embed(),
            view=MainView(self.cog)
        )


# ================= USER LIST =================

class UserListView(discord.ui.View):
    def __init__(self, cog):
        super().__init__(timeout=180)
        self.cog = cog

        guild_data = cog.data.get(str(cog.bot.guilds[0].id), {})
        users = guild_data.get("users", {})

        options = []
        for uid in users:
            options.append(discord.SelectOption(label=f"User {uid}", value=uid))

        if options:
            self.add_item(UserSelectDropdown(cog, options))
        else:
            self.add_item(discord.ui.Button(label="🍄‍🟫ไม่มีข้อมูล", disabled=True))

        self.add_item(CancelButton(cog))


class UserSelectDropdown(discord.ui.Select):
    def __init__(self, cog, options):
        super().__init__(placeholder="🍇เลือกผู้ใช้", options=options)
        self.cog = cog

    async def callback(self, interaction):
        guild_id = str(interaction.guild.id)
        data = self.cog.data[guild_id]["users"][self.values[0]]
        member = interaction.guild.get_member(int(self.values[0]))

        embed = discord.Embed(
            title=f"👤 {member}",
            color=discord.Color.blurple()
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.add_field(name="สิทธิ์ที่ได้รับ", value=format_permissions(data))

        await interaction.response.edit_message(
            embed=embed,
            view=RemoveUserView(self.cog, self.values[0])
        )


class RemoveUserView(discord.ui.View):
    def __init__(self, cog, user_id):
        super().__init__(timeout=180)
        self.cog = cog
        self.user_id = user_id

    @discord.ui.button(label="🗑 ลบออก", style=discord.ButtonStyle.danger)
    async def remove(self, interaction, button):
        guild_id = str(interaction.guild.id)
        del self.cog.data[guild_id]["users"][self.user_id]
        self.cog.save_data()

        await interaction.response.edit_message(
            embed=discord.Embed(description="🥝 ลบออกจาก Whitelist แล้ว"),
            view=MainView(self.cog)
        )

    @discord.ui.button(label="🍉 ยกเลิก", style=discord.ButtonStyle.secondary)
    async def cancel(self, interaction, button):
        await interaction.response.edit_message(
            embed=main_embed(),
            view=MainView(self.cog)
        )


# ================= ROLE LIST =================

class RoleListView(discord.ui.View):
    def __init__(self, cog):
        super().__init__(timeout=180)
        self.cog = cog

        guild_data = cog.data.get(str(cog.bot.guilds[0].id), {})
        roles = guild_data.get("roles", {})

        options = []
        for rid in roles:
            options.append(discord.SelectOption(label=f"Role {rid}", value=rid))

        if options:
            self.add_item(RoleSelectDropdown(cog, options))
        else:
            self.add_item(discord.ui.Button(label="🍎ไม่มีข้อมูล", disabled=True))

        self.add_item(CancelButton(cog))


class RoleSelectDropdown(discord.ui.Select):
    def __init__(self, cog, options):
        super().__init__(placeholder="🌽เลือกบทบาท", options=options)
        self.cog = cog

    async def callback(self, interaction):
        guild_id = str(interaction.guild.id)
        data = self.cog.data[guild_id]["roles"][self.values[0]]
        role = interaction.guild.get_role(int(self.values[0]))

        embed = discord.Embed(
            title=f"🛡 {role.name}",
            color=role.color
        )
        embed.add_field(name="🥕สิทธิ์ที่ได้รับ", value=format_permissions(data))

        await interaction.response.edit_message(
            embed=embed,
            view=RemoveRoleView(self.cog, self.values[0])
        )


class RemoveRoleView(discord.ui.View):
    def __init__(self, cog, role_id):
        super().__init__(timeout=180)
        self.cog = cog
        self.role_id = role_id

    @discord.ui.button(label="🗑 ลบออก", style=discord.ButtonStyle.danger)
    async def remove(self, interaction, button):
        guild_id = str(interaction.guild.id)
        del self.cog.data[guild_id]["roles"][self.role_id]
        self.cog.save_data()

        await interaction.response.edit_message(
            embed=discord.Embed(description="🥬 ลบออกจาก Whitelist แล้ว"),
            view=MainView(self.cog)
        )

    @discord.ui.button(label="🌶️ ยกเลิก", style=discord.ButtonStyle.secondary)
    async def cancel(self, interaction, button):
        await interaction.response.edit_message(
            embed=main_embed(),
            view=MainView(self.cog)
        )


class CancelButton(discord.ui.Button):
    def __init__(self, cog):
        super().__init__(label="🌶️ ยกเลิก", style=discord.ButtonStyle.secondary)
        self.cog = cog

    async def callback(self, interaction):
        await interaction.response.edit_message(
            embed=main_embed(),
            view=MainView(self.cog)
        )


async def setup(bot):
    await bot.add_cog(Whitelist(bot))