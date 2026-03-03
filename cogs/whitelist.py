import discord
from discord.ext import commands
from discord import app_commands

permissions = {}
anti_spam_status = {}


def get_guild_data(guild_id: int):
    if guild_id not in permissions:
        permissions[guild_id] = {"users": {}, "roles": {}}
    return permissions[guild_id]


class TargetSelect(discord.ui.View):
    def __init__(self, guild_id: int):
        super().__init__(timeout=120)
        self.guild_id = guild_id

    @discord.ui.button(label="เลือกผู้ใช้", style=discord.ButtonStyle.secondary)
    async def user_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(UserModal(self.guild_id))

    @discord.ui.button(label="เลือกยศ", style=discord.ButtonStyle.secondary)
    async def role_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(RoleModal(self.guild_id))


class UserModal(discord.ui.Modal, title="ใส่ไอดีผู้ใช้"):
    user_id = discord.ui.TextInput(label="User ID")

    def __init__(self, guild_id: int):
        super().__init__()
        self.guild_id = guild_id

    async def on_submit(self, interaction: discord.Interaction):
        if not interaction.guild:
            return

        try:
            uid = int(self.user_id.value)
        except ValueError:
            return await interaction.response.send_message("ไอดีไม่ถูกต้อง", ephemeral=True)

        member = interaction.guild.get_member(uid)
        if not member:
            return await interaction.response.send_message("ไม่พบผู้ใช้", ephemeral=True)

        embed = discord.Embed(
            title="จัดการผู้ใช้",
            description=f"กำลังตั้งค่าให้ {member.mention}",
            color=discord.Color.dark_gray()
        )

        await interaction.response.send_message(
            embed=embed,
            view=PermissionView(self.guild_id, "users", uid),
            ephemeral=True
        )


class RoleModal(discord.ui.Modal, title="ใส่ไอดียศ"):
    role_id = discord.ui.TextInput(label="Role ID")

    def __init__(self, guild_id: int):
        super().__init__()
        self.guild_id = guild_id

    async def on_submit(self, interaction: discord.Interaction):
        if not interaction.guild:
            return

        try:
            rid = int(self.role_id.value)
        except ValueError:
            return await interaction.response.send_message("ไอดีไม่ถูกต้อง", ephemeral=True)

        role = interaction.guild.get_role(rid)
        if not role:
            return await interaction.response.send_message("ไม่พบยศ", ephemeral=True)

        embed = discord.Embed(
            title="จัดการยศ",
            description=f"กำลังตั้งค่าให้ {role.mention}",
            color=discord.Color.dark_gray()
        )

        await interaction.response.send_message(
            embed=embed,
            view=PermissionView(self.guild_id, "roles", rid),
            ephemeral=True
        )


class PermissionView(discord.ui.View):
    def __init__(self, guild_id: int, target_type: str, target_id: int):
        super().__init__(timeout=120)
        self.guild_id = guild_id
        self.target_type = target_type
        self.target_id = target_id

    @discord.ui.button(label="อนุญาต Anti-Spam", style=discord.ButtonStyle.secondary)
    async def allow_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        data = get_guild_data(self.guild_id)

        if self.target_id not in data[self.target_type]:
            data[self.target_type][self.target_id] = {}

        data[self.target_type][self.target_id]["anti_spam"] = True

        await interaction.response.edit_message(content="อนุญาตแล้ว", view=self)

    @discord.ui.button(label="ลบออกจากระบบ", style=discord.ButtonStyle.secondary)
    async def remove_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        data = get_guild_data(self.guild_id)

        if self.target_id in data[self.target_type]:
            del data[self.target_type][self.target_id]

        await interaction.response.edit_message(content="ลบออกแล้ว", view=None)

    @discord.ui.button(label="ย้อนกลับ", style=discord.ButtonStyle.secondary)
    async def back_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(view=TargetSelect(self.guild_id))


class AntiMainView(discord.ui.View):
    def __init__(self, guild_id: int):
        super().__init__(timeout=120)
        self.guild_id = guild_id

    @discord.ui.button(label="เปิด/ปิด ระบบ", style=discord.ButtonStyle.secondary)
    async def toggle_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        anti_spam_status[self.guild_id] = not anti_spam_status.get(self.guild_id, False)

        status = "เปิด" if anti_spam_status[self.guild_id] else "ปิด"

        embed = discord.Embed(
            title="ระบบ Anti-Spam",
            description=f"สถานะปัจจุบัน: {status}",
            color=discord.Color.dark_gray()
        )

        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="จัดการสิทธิ์", style=discord.ButtonStyle.secondary)
    async def manage_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(view=TargetSelect(self.guild_id))


class Virus(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="anti", description="จัดการระบบ Anti-Spam")
    @app_commands.default_permissions(administrator=True)
    async def anti(self, interaction: discord.Interaction):
        if not interaction.guild:
            return await interaction.response.send_message("ใช้ได้เฉพาะในเซิร์ฟเวอร์", ephemeral=True)

        if not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message("เฉพาะแอดมินเท่านั้น", ephemeral=True)

        guild_id = interaction.guild.id
        status = anti_spam_status.get(guild_id, False)

        embed = discord.Embed(
            title="ระบบ Anti-Spam",
            description=f"สถานะปัจจุบัน: {'เปิด' if status else 'ปิด'}",
            color=discord.Color.dark_gray()
        )

        await interaction.response.send_message(
            embed=embed,
            view=AntiMainView(guild_id),
            ephemeral=True
        )


async def setup(bot):
    await bot.add_cog(Virus(bot))