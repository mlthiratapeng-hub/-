import discord
from discord.ext import commands
from discord import app_commands
import time

TRIGGER_NAME = "สร้างห้องส่วนตัว"


class VoiceControl(discord.ui.View):

    def __init__(self, owner_id, voice_channel):
        super().__init__(timeout=None)
        self.owner_id = owner_id
        self.voice_channel = voice_channel

    @discord.ui.select(
        placeholder="เลือกจำนวนคนในห้อง",
        options=[
            discord.SelectOption(label="2"),
            discord.SelectOption(label="4"),
            discord.SelectOption(label="6"),
            discord.SelectOption(label="8"),
            discord.SelectOption(label="10"),
            discord.SelectOption(label="15"),
            discord.SelectOption(label="20"),
            discord.SelectOption(label="25"),
            discord.SelectOption(label="50"),
            discord.SelectOption(label="99"),
        ]
    )
    async def select_limit(self, interaction: discord.Interaction, select: discord.ui.Select):

        if interaction.user.id != self.owner_id:
            await interaction.response.send_message("🌶️ เฉพาะเจ้าของห้องเท่านั้น", ephemeral=True)
            return

        limit = int(select.values[0])
        await self.voice_channel.edit(user_limit=limit)

        await interaction.response.send_message(
            f"🍃 ตั้งค่าห้อง {limit} คน",
            ephemeral=True
        )

    @discord.ui.button(label="Lock", emoji="🔒", style=discord.ButtonStyle.red)
    async def lock(self, interaction: discord.Interaction, button: discord.ui.Button):

        if interaction.user.id != self.owner_id:
            await interaction.response.send_message("🍅 เฉพาะเจ้าของห้อง", ephemeral=True)
            return

        await self.voice_channel.set_permissions(
            interaction.guild.default_role,
            connect=False
        )

        await interaction.response.send_message("🔒 ล็อคห้องแล้ว", ephemeral=True)

    @discord.ui.button(label="Unlock", emoji="🔓", style=discord.ButtonStyle.green)
    async def unlock(self, interaction: discord.Interaction, button: discord.ui.Button):

        if interaction.user.id != self.owner_id:
            await interaction.response.send_message("🌶️ เฉพาะเจ้าของห้อง", ephemeral=True)
            return

        await self.voice_channel.set_permissions(
            interaction.guild.default_role,
            connect=True
        )

        await interaction.response.send_message("🔓 ปลดล็อคห้องแล้ว", ephemeral=True)


class PrivateVoice(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.trigger_channel = None
        self.cooldown = {}

    # ------------------
    # slash command
    # ------------------
    @app_commands.command(name="Create_a_voice", description="สร้างระบบห้องส่วนตัว")
    async def create_voice(self, interaction: discord.Interaction):

        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message(
                "🍒 คำสั่งนี้สำหรับแอดมินเท่านั้นค่ะ",
                ephemeral=True
            )
            return

        channel = await interaction.guild.create_voice_channel(TRIGGER_NAME)

        self.trigger_channel = channel.id

        await interaction.response.send_message(
            f"🍇 สร้างห้องแล้ว {channel.mention}",
            ephemeral=True
        )

    # ------------------
    # voice system
    # ------------------
    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):

        # เข้า trigger room
        if after.channel and after.channel.id == self.trigger_channel:

            now = time.time()

            if member.id in self.cooldown:
                if now - self.cooldown[member.id] < 10:
                    await member.move_to(None)
                    return

            self.cooldown[member.id] = now

            guild = member.guild

            private = await guild.create_voice_channel(
                name=f"Private-{member.name}",
                category=after.channel.category
            )

            await member.move_to(private)

            embed = discord.Embed(
                title="📁 Voice Control",
                description="ปรับแต่งห้องของคุณ",
                color=discord.Color.green()
            )

            view = VoiceControl(member.id, private)

            await private.send(embed=embed, view=view)

        # ลบห้องถ้าไม่มีคน
        if before.channel:

            if before.channel.name.startswith("Private-"):

                if len(before.channel.members) == 0:
                    await before.channel.delete()


async def setup(bot):
    await bot.add_cog(PrivateVoice(bot))