import discord
from discord.ext import commands
from discord import app_commands

# โครงสร้าง:
# prevent_data[guild_id] = {
#     "users": {
#         user_id: {"link":bool,"spam":bool,"nuke":bool}
#     },
#     "roles": {
#         role_id: {"link":bool,"spam":bool,"nuke":bool}
#     }
# }

prevent_data = {}


# ================= HELPER =================

def is_prevented(member: discord.Member, system: str):
    guild_id = member.guild.id

    if guild_id not in prevent_data:
        return False

    data = prevent_data[guild_id]

    # เช็ค user
    user_data = data["users"].get(member.id)
    if user_data and user_data.get(system):
        return True

    # เช็ค role
    for role in member.roles:
        role_data = data["roles"].get(role.id)
        if role_data and role_data.get(system):
            return True

    return False


# ================= VIEW =================

class PreventMainView(discord.ui.View):
    def __init__(self, guild_id):
        super().__init__(timeout=120)
        self.guild_id = guild_id

    @discord.ui.button(label="1️⃣ จัดการ Prevent", style=discord.ButtonStyle.primary)
    async def manage(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(
            embed=discord.Embed(
                title="⚙️ จัดการ Prevent",
                description="เลือกว่าจะอนุญาต ผู้ใช้ หรือ ยศ",
                color=discord.Color.blurple()
            ),
            view=PreventSelectTypeView(self.guild_id)
        )

    @discord.ui.button(label="2️⃣ ดูรายการ Prevent", style=discord.ButtonStyle.secondary)
    async def list_all(self, interaction: discord.Interaction, button: discord.ui.Button):

        data = prevent_data.get(self.guild_id, {"users":{}, "roles":{}})

        desc = ""

        for uid in data["users"]:
            desc += f"👤 <@{uid}>\n"

        for rid in data["roles"]:
            desc += f"🎖️ <@&{rid}>\n"

        if desc == "":
            desc = "ไม่มีรายการ"

        embed = discord.Embed(
            title="📋 รายการ Prevent",
            description=desc,
            color=discord.Color.greyple()
        )

        await interaction.response.edit_message(embed=embed, view=self)


class PreventSelectTypeView(discord.ui.View):
    def __init__(self, guild_id):
        super().__init__(timeout=120)
        self.guild_id = guild_id

    @discord.ui.select(
        placeholder="เลือกประเภท...",
        options=[
            discord.SelectOption(label="👤 ผู้ใช้", value="user"),
            discord.SelectOption(label="🎖️ ยศ", value="role")
        ]
    )
    async def select_type(self, interaction: discord.Interaction, select: discord.ui.Select):

        if select.values[0] == "user":
            await interaction.response.edit_message(
                embed=discord.Embed(
                    title="👤 เลือกผู้ใช้",
                    description="🍲 เลือกผู้ใช้ด้านล่าง",
                    color=discord.Color.blue()
                ),
                view=PreventUserSelectView(self.guild_id)
            )
        else:
            await interaction.response.edit_message(
                embed=discord.Embed(
                    title="🎖️ เลือกยศ",
                    description="🍇 เลือกยศด้านล่าง",
                    color=discord.Color.orange()
                ),
                view=PreventRoleSelectView(self.guild_id)
            )


class PreventUserSelectView(discord.ui.View):
    def __init__(self, guild_id):
        super().__init__(timeout=120)
        self.guild_id = guild_id

        self.add_item(discord.ui.UserSelect())

    async def interaction_check(self, interaction):
        return True

    @discord.ui.button(label="🕸️ ต่อไป", style=discord.ButtonStyle.success)
    async def next(self, interaction: discord.Interaction, button: discord.ui.Button):
        user = interaction.data["resolved"]["users"]
        user_id = int(list(user.keys())[0])

        await interaction.response.edit_message(
            embed=discord.Embed(
                title="🔐 เลือกระบบที่จะยกเว้น",
                description="🍧 เลือกด้านล่าง",
                color=discord.Color.green()
            ),
            view=PreventSystemView(self.guild_id, user_id, "user")
        )


class PreventRoleSelectView(discord.ui.View):
    def __init__(self, guild_id):
        super().__init__(timeout=120)
        self.guild_id = guild_id
        self.add_item(discord.ui.RoleSelect())

    @discord.ui.button(label="ต่อไป", style=discord.ButtonStyle.success)
    async def next(self, interaction: discord.Interaction, button: discord.ui.Button):
        role = interaction.data["resolved"]["roles"]
        role_id = int(list(role.keys())[0])

        await interaction.response.edit_message(
            embed=discord.Embed(
                title="🔐 เลือกระบบที่จะยกเว้น",
                description="🥡 เลือกด้านล่าง",
                color=discord.Color.green()
            ),
            view=PreventSystemView(self.guild_id, role_id, "role")
        )


class PreventSystemView(discord.ui.View):
    def __init__(self, guild_id, target_id, target_type):
        super().__init__(timeout=120)
        self.guild_id = guild_id
        self.target_id = target_id
        self.target_type = target_type

        self.link = False
        self.spam = False
        self.nuke = False

    @discord.ui.button(label="🔗 Anti-Link", style=discord.ButtonStyle.primary)
    async def link_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.link = not self.link
        await interaction.response.defer()

    @discord.ui.button(label="🗣️ Anti-Spam", style=discord.ButtonStyle.primary)
    async def spam_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.spam = not self.spam
        await interaction.response.defer()

    @discord.ui.button(label="💣 Anti-Nuke", style=discord.ButtonStyle.primary)
    async def nuke_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.nuke = not self.nuke
        await interaction.response.defer()

    @discord.ui.button(label="📂 บันทึก", style=discord.ButtonStyle.success)
    async def save(self, interaction: discord.Interaction, button: discord.ui.Button):

        if self.guild_id not in prevent_data:
            prevent_data[self.guild_id] = {"users":{}, "roles":{}}

        prevent_data[self.guild_id][
            "users" if self.target_type=="user" else "roles"
        ][self.target_id] = {
            "link": self.link,
            "spam": self.spam,
            "nuke": self.nuke
        }

        await interaction.response.edit_message(
            embed=discord.Embed(
                title="🍃 บันทึกสำเร็จ",
                description="📁 ระบบจะไม่ตรวจสอบเป้าหมายนี้ตามที่เลือก",
                color=discord.Color.green()
            ),
            view=None
        )

    @discord.ui.button(label="🗑️ ลบข้อมูล", style=discord.ButtonStyle.danger)
    async def delete(self, interaction: discord.Interaction, button: discord.ui.Button):

        data = prevent_data.get(self.guild_id)

        if data:
            container = data["users"] if self.target_type=="user" else data["roles"]
            container.pop(self.target_id, None)

        await interaction.response.edit_message(
            embed=discord.Embed(
                title="🗑️ ลบข้อมูลสำเร็จ",
                color=discord.Color.red()
            ),
            view=None
        )


# ================= COG =================

class Prevent(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="prevent", description="ป้องกันการตรวจสอบจากระบบ Anti")
    async def prevent(self, interaction: discord.Interaction):

        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message(
                "ใช้ได้เฉพาะแอดมินนะค่ะ",
                ephemeral=True
            )
            return

        guild_id = interaction.guild.id

        if guild_id not in prevent_data:
            prevent_data[guild_id] = {"users":{}, "roles":{}}

        embed = discord.Embed(
            title="🛡️ ระบบ Prevent",
            description="🍃 เลือกเมนูด้านล่างได้เยยย",
            color=discord.Color.blurple()
        )

        await interaction.response.send_message(
            embed=embed,
            view=PreventMainView(guild_id),
            ephemeral=True
        )


async def setup(bot):
    await bot.add_cog(Prevent(bot))