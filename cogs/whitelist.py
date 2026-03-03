import discord
from discord.ext import commands
from discord import app_commands

# ==========================================
# VIEW หลัก
# ==========================================

class WhitelistMainView(discord.ui.View):
    def __init__(self, cog):
        super().__init__(timeout=300)
        self.cog = cog

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("🍎 Admin เท่านั้น", ephemeral=True)
            return False
        return True

    # =========================
    # เพิ่ม / แก้ไข
    # =========================
    @discord.ui.button(label="🌶 เพิ่ม / แก้ไข", style=discord.ButtonStyle.green)
    async def add_edit(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(
            "👤 เลือกผู้ใช้ที่ต้องการเพิ่มเข้า Whitelist",
            view=WhitelistSelectUserView(self.cog),
            ephemeral=True
        )

    # =========================
    # ดูรายการ
    # =========================
    @discord.ui.button(label="📋 ดูรายการ", style=discord.ButtonStyle.blurple)
    async def list_btn(self, interaction: discord.Interaction, button: discord.ui.Button):

        if not self.cog.whitelist:
            return await interaction.response.send_message(
                "📄 ยังไม่มีใครอยู่ใน Whitelist",
                ephemeral=True
            )

        users = "\n".join([f"<@{uid}>" for uid in self.cog.whitelist])

        embed = discord.Embed(
            title="📄 รายชื่อ Whitelist",
            description=users,
            color=discord.Color.green()
        )

        await interaction.response.send_message(embed=embed, ephemeral=True)

    # =========================
    # ปิด
    # =========================
    @discord.ui.button(label="🍒 ปิด", style=discord.ButtonStyle.gray)
    async def close_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(content="🔒 ปิดเมนูแล้ว", view=None)


# ==========================================
# VIEW เลือกผู้ใช้
# ==========================================

class WhitelistSelectUserView(discord.ui.View):
    def __init__(self, cog):
        super().__init__(timeout=300)
        self.cog = cog

    @discord.ui.user_select(placeholder="เลือกผู้ใช้...", min_values=1, max_values=1)
    async def select_user(self, interaction: discord.Interaction, select: discord.ui.UserSelect):

        user = select.values[0]

        embed = discord.Embed(
            title="👤 โปรไฟล์ผู้ใช้",
            description=f"ต้องการเพิ่ม {user.mention} เข้า Whitelist หรือไม่?",
            color=discord.Color.orange()
        )
        embed.set_thumbnail(url=user.display_avatar.url)

        await interaction.response.edit_message(
            embed=embed,
            view=WhitelistConfirmView(self.cog, user)
        )

    @discord.ui.button(label="⬅ ย้อนกลับ", style=discord.ButtonStyle.secondary)
    async def back_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(
            content="📂 ระบบ Whitelist\nเลือกเมนูด้านล่าง",
            embed=None,
            view=WhitelistMainView(self.cog)
        )


# ==========================================
# VIEW ยืนยันเพิ่ม/ลบ
# ==========================================

class WhitelistConfirmView(discord.ui.View):
    def __init__(self, cog, user):
        super().__init__(timeout=300)
        self.cog = cog
        self.user = user

    # เพิ่ม
    @discord.ui.button(label="🥭 เพิ่ม", style=discord.ButtonStyle.green)
    async def confirm_add(self, interaction: discord.Interaction, button: discord.ui.Button):

        self.cog.whitelist.add(self.user.id)

        await interaction.response.edit_message(
            content=f"🥕 เพิ่ม {self.user.mention} เข้า Whitelist แล้ว",
            embed=None,
            view=WhitelistAfterView(self.cog)
        )

    # ลบ
    @discord.ui.button(label="🗑 ลบ", style=discord.ButtonStyle.red)
    async def confirm_remove(self, interaction: discord.Interaction, button: discord.ui.Button):

        self.cog.whitelist.discard(self.user.id)

        await interaction.response.edit_message(
            content=f"🌶️ ลบ {self.user.mention} ออกจาก Whitelist แล้ว",
            embed=None,
            view=WhitelistAfterView(self.cog)
        )

    # ยกเลิก
    @discord.ui.button(label="🍅 ยกเลิก", style=discord.ButtonStyle.gray)
    async def cancel_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(
            content="🍈 ยกเลิกแล้ว",
            embed=None,
            view=WhitelistMainView(self.cog)
        )


# ==========================================
# VIEW หลังทำรายการเสร็จ
# ==========================================

class WhitelistAfterView(discord.ui.View):
    def __init__(self, cog):
        super().__init__(timeout=300)
        self.cog = cog

    @discord.ui.button(label="⬅ กลับหน้าแรก", style=discord.ButtonStyle.secondary)
    async def back_main(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(
            content="📂 ระบบ Whitelist\nเลือกเมนูด้านล่าง",
            view=WhitelistMainView(self.cog)
        )


# ==========================================
# COG
# ==========================================

class Whitelist(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.whitelist = set()

    # ==========================================
    # Slash Command
    # ==========================================
    @app_commands.command(name="whitelist", description="ระบบจัดการ Whitelist")
    async def whitelist(self, interaction: discord.Interaction):

        if not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message(
                "❌ Admin เท่านั้น",
                ephemeral=True
            )

        embed = discord.Embed(
            title="📂 ระบบ Whitelist",
            description="เลือกเมนูด้านล่าง",
            color=discord.Color.purple()
        )

        await interaction.response.send_message(
            embed=embed,
            view=WhitelistMainView(self),
            ephemeral=True
        )

    # ==========================================
    # ใช้กับ anti-link / anti-spam / anti-nuke
    # ==========================================
    def is_whitelisted(self, user_id: int):
        return user_id in self.whitelist


# ==========================================
# SETUP
# ==========================================

async def setup(bot: commands.Bot):
    await bot.add_cog(Whitelist(bot))