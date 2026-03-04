import discord
from discord.ext import commands
from discord import app_commands
import re
import sqlite3

# ================= DATABASE =================

conn = sqlite3.connect("antilink.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS antilink (
    guild_id INTEGER PRIMARY KEY,
    mode INTEGER DEFAULT 0,
    max_warn INTEGER DEFAULT 3,
    whitelist_role INTEGER
)
""")
conn.commit()


def get_settings(guild_id: int):
    cursor.execute("SELECT mode, max_warn, whitelist_role FROM antilink WHERE guild_id=?", (guild_id,))
    data = cursor.fetchone()

    if data is None:
        cursor.execute("INSERT INTO antilink (guild_id) VALUES (?)", (guild_id,))
        conn.commit()
        return 0, 3, None

    return data


def update_setting(guild_id: int, column: str, value):
    cursor.execute(f"UPDATE antilink SET {column}=? WHERE guild_id=?", (value, guild_id))
    conn.commit()


# ================= VIEW =================

class AntiLinkView(discord.ui.View):
    def __init__(self, guild_id: int):
        super().__init__(timeout=60)
        self.guild_id = guild_id

    async def update_embed(self, interaction, text, color):
        embed = discord.Embed(
            title="🔗 ระบบป้องกันลิงก์",
            description=text,
            color=color
        )
        await interaction.response.edit_message(embed=embed, view=None)

    @discord.ui.button(label="1️⃣ กัน Invite อย่างเดียว", style=discord.ButtonStyle.primary)
    async def invite_only(self, interaction: discord.Interaction, button: discord.ui.Button):
        update_setting(self.guild_id, "mode", 1)
        await self.update_embed(interaction, "เปิดโหมด: กันเฉพาะลิงก์เชิญ Discord", discord.Color.blue())

    @discord.ui.button(label="2️⃣ กันลิงก์ภายนอก", style=discord.ButtonStyle.success)
    async def external_only(self, interaction: discord.Interaction, button: discord.ui.Button):
        update_setting(self.guild_id, "mode", 2)
        await self.update_embed(interaction, "เปิดโหมด: กันลิงก์ภายนอก (อนุญาต Invite)", discord.Color.green())

    @discord.ui.button(label="3️⃣ กันทุกลิงก์", style=discord.ButtonStyle.danger)
    async def all_links(self, interaction: discord.Interaction, button: discord.ui.Button):
        update_setting(self.guild_id, "mode", 3)
        await self.update_embed(interaction, "เปิดโหมด: กันทุกลิงก์", discord.Color.red())

    @discord.ui.button(label="❌ ปิดระบบ", style=discord.ButtonStyle.secondary)
    async def disable(self, interaction: discord.Interaction, button: discord.ui.Button):
        update_setting(self.guild_id, "mode", 0)
        await self.update_embed(interaction, "ปิดระบบป้องกันลิงก์แล้ว", discord.Color.greyple())


# ================= COG =================

class AntiLink(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.warnings = {}

    # ===== Slash Command เปิดเมนู =====
    @app_commands.command(name="anti-link", description="ตั้งค่าระบบป้องกันลิงก์")
    async def anti_link(self, interaction: discord.Interaction):

        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ ใช้ได้เฉพาะแอดมิน", ephemeral=True)
            return

        guild_id = interaction.guild.id
        mode, max_warn, whitelist_role = get_settings(guild_id)

        mode_text = {
            0: "❌ ปิดอยู่",
            1: "กันเฉพาะ Invite",
            2: "กันลิงก์ภายนอก",
            3: "กันทุกลิงก์"
        }

        embed = discord.Embed(
            title="🔗 ตั้งค่าระบบป้องกันลิงก์",
            color=discord.Color.blurple()
        )

        embed.add_field(name="สถานะ", value=mode_text[mode], inline=False)
        embed.add_field(name="เตือนก่อนแบน", value=f"{max_warn} ครั้ง", inline=False)

        if whitelist_role:
            role = interaction.guild.get_role(whitelist_role)
            embed.add_field(name="Whitelist Role", value=role.mention if role else "ไม่พบ", inline=False)
        else:
            embed.add_field(name="Whitelist Role", value="ไม่มี", inline=False)

        await interaction.response.send_message(embed=embed, view=AntiLinkView(guild_id), ephemeral=True)

    # ===== ตั้งจำนวนเตือน =====
    @app_commands.command(name="set-warn", description="ตั้งค่าจำนวนครั้งก่อนแบน")
    async def set_warn(self, interaction: discord.Interaction, amount: int):

        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ ใช้ได้เฉพาะแอดมิน", ephemeral=True)
            return

        if amount < 1:
            await interaction.response.send_message("จำนวนต้องมากกว่า 0", ephemeral=True)
            return

        update_setting(interaction.guild.id, "max_warn", amount)
        await interaction.response.send_message(f"ตั้งค่าเตือนก่อนแบน = {amount} ครั้งแล้ว", ephemeral=True)

    # ===== ตั้ง Whitelist Role =====
    @app_commands.command(name="set-whitelist", description="ตั้ง Role ที่ส่งลิงก์ได้")
    async def set_whitelist(self, interaction: discord.Interaction, role: discord.Role):

        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ ใช้ได้เฉพาะแอดมิน", ephemeral=True)
            return

        update_setting(interaction.guild.id, "whitelist_role", role.id)
        await interaction.response.send_message(f"ตั้งค่า {role.mention} เป็น Whitelist แล้ว", ephemeral=True)

    # ===== ตรวจข้อความ =====
    @commands.Cog.listener()
    async def on_message(self, message):

        if message.author.bot or not message.guild:
            return

        guild_id = message.guild.id
        mode, max_warn, whitelist_role = get_settings(guild_id)

        if mode == 0:
            return

        if whitelist_role and discord.utils.get(message.author.roles, id=whitelist_role):
            return

        content = message.content.lower()

        has_link = re.search(r"https?://", content)
        has_invite = re.search(r"(discord\.gg/|discord\.com/invite/)", content)

        violation = False

        if mode == 1 and has_invite:
            violation = True
        elif mode == 2 and has_link and not has_invite:
            violation = True
        elif mode == 3 and has_link:
            violation = True

        if not violation:
            return

        try:
            await message.delete()
        except:
            pass

        key = (guild_id, message.author.id)
        self.warnings[key] = self.warnings.get(key, 0) + 1
        count = self.warnings[key]

        if count < max_warn:
            await message.channel.send(
                f"⚠️ {message.author.mention} ห้ามส่งลิงก์ ({count}/{max_warn})",
                delete_after=5
            )
            return

        try:
            await message.author.ban(reason="ส่งลิงก์เกินกำหนด")
            await message.channel.send(
                f"🔨 {message.author.mention} ถูกแบน (ส่งลิงก์ครบ {max_warn} ครั้ง)",
                delete_after=5
            )
        except Exception as e:
            print("BAN ERROR:", e)

        self.warnings.pop(key, None)


# ================= SETUP =================

async def setup(bot):
    await bot.add_cog(AntiLink(bot))