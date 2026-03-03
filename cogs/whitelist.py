import discord
from discord.ext import commands
from discord import app_commands

# =========================
# เก็บข้อมูล
# =========================

permissions = {}
# โครงสร้าง
# permissions[guild_id] = {
#     "users": {user_id: {"anti_spam": True}},
#     "roles": {role_id: {"anti_spam": True}}
# }

anti_spam_status = {}  # เปิด/ปิดระบบต่อเซิร์ฟเวอร์


def get_guild_data(guild_id):
    if guild_id not in permissions:
        permissions[guild_id] = {"users": {}, "roles": {}}
    return permissions[guild_id]


# =========================
# VIEW เลือก User / Role
# =========================

class TargetSelect(discord.ui.View):
    def __init__(self, guild_id):
        super().__init__(timeout=120)
        self.guild_id = guild_id

    @discord.ui.button(label="เลือกผู้ใช้", style=discord.ButtonStyle.secondary)
    async def user_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(UserModal(self.guild_id))

    @discord.ui.button(label="🍄‍🟫เลือกยศ", style=discord.ButtonStyle.secondary)
    async def role_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(RoleModal(self.guild_id))


# =========================
# MODAL ผู้ใช้
# =========================

class UserModal(discord.ui.Modal, title="ใส่ไอดีผู้ใช้"):
    user_id = discord.ui.TextInput(label="User ID", placeholder="ใส่ไอดีผู้ใช้")

    def __init__(self, guild_id):
        super().__init__()
        self.guild_id = guild_id

    async def on_submit(self, interaction: discord.Interaction):
        try:
            user_id = int(self.user_id.value)
        except:
            return await interaction.response.send_message("🍎 ไอดีไม่ถูกต้อง", ephemeral=True)

        member = interaction.guild.get_member(user_id)
        if not member:
            return await interaction.response.send_message("🍓 ไม่พบผู้ใช้", ephemeral=True)

        embed = discord.Embed(
            title="จัดการผู้ใช้",
            description=f"กำลังตั้งค่าให้ {member.mention}",
            color=discord.Color.dark_gray()
        )
        embed.set_thumbnail(url=member.display_avatar.url)

        await interaction.response.send_message(
            embed=embed,
            view=PermissionView(self.guild_id, "users", member.id),
            ephemeral=True
        )


# =========================
# MODAL ยศ
# =========================

class RoleModal(discord.ui.Modal, title="ใส่ไอดียศ"):
    role_id = discord.ui.TextInput(label="Role ID", placeholder="ใส่ไอดียศ")

    def __init__(self, guild_id):
        super().__init__()
        self.guild_id = guild_id

    async def on_submit(self, interaction: discord.Interaction):
        try:
            role_id = int(self.role_id.value)
        except:
            return await interaction.response.send_message("🍎 ไอดีไม่ถูกต้อง", ephemeral=True)

        role = interaction.guild.get_role(role_id)
        if not role:
            return await interaction.response.send_message("🌶️ ไม่พบยศ", ephemeral=True)

        embed = discord.Embed(
            title="🥕จัดการยศ",
            description=f"🍃กำลังตั้งค่าให้ {role.mention}",
            color=discord.Color.dark_gray()
        )
        embed.set_thumbnail(url=interaction.guild.me.display_avatar.url)

        await interaction.response.send_message(
            embed=embed,
            view=PermissionView(self.guild_id, "roles", role.id),
            ephemeral=True
        )


# =========================
# VIEW ตั้งค่าสิทธิ์
# =========================

class PermissionView(discord.ui.View):
    def __init__(self, guild_id, target_type, target_id):
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

        await interaction.response.edit_message(content="🥝 อนุญาตแล้ว", view=self)

    @discord.ui.button(label="ลบออกจากระบบ", style=discord.ButtonStyle.secondary)
    async def remove_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        data = get_guild_data(self.guild_id)
        if self.target_id in data[self.target_type]:
            del data[self.target_type][self.target_id]

        await interaction.response.edit_message(content="🍃 ลบออกแล้ว", view=None)

    @discord.ui.button(label="ย้อนกลับ", style=discord.ButtonStyle.secondary)
    async def back_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(
            content="🍇เลือกใหม่",
            embed=None,
            view=TargetSelect(self.guild_id)
        )


# =========================
# COG
# =========================

class Virus(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="anti", description="📁จัดการระบบ Anti-Spam")
    @app_commands.checks.has_permissions(administrator=True)  # จำกัดแอดมินเท่านั้น
    async def anti(self, interaction: discord.Interaction):

        guild_id = interaction.guild.id

        if guild_id not in anti_spam_status:
            anti_spam_status[guild_id] = False

        embed = discord.Embed(
            title="ระบบ Anti-Spam",
            description="🕸️เลือกจัดการด้านล่าง",
            color=discord.Color.dark_gray()
        )

        embed.add_field(
            name="สถานะปัจจุบัน",
            value="🍈 เปิด" if anti_spam_status[guild_id] else "🍅 ปิด",
            inline=False
        )

        await interaction.response.send_message(
            embed=embed,
            view=TargetSelect(guild_id),
            ephemeral=True
        )


async def setup(bot):
    await bot.add_cog(Virus(bot))