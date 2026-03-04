import discord
from discord import app_commands
from discord.ext import commands

class Invitation(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.welcome_channel = {}  # เก็บ channel แบบชั่วคราว
        self.invites_cache = {}

    async def cog_load(self):
        for guild in self.bot.guilds:
            self.invites_cache[guild.id] = await guild.invites()

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        self.invites_cache[guild.id] = await guild.invites()

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        guild = member.guild

        if guild.id not in self.welcome_channel:
            return

        channel_id = self.welcome_channel[guild.id]
        channel = guild.get_channel(channel_id)
        if not channel:
            return

        old_invites = self.invites_cache.get(guild.id, [])
        new_invites = await guild.invites()

        inviter = "ไม่ทราบ"
        invite_count = 0

        for invite in new_invites:
            for old in old_invites:
                if invite.code == old.code and invite.uses > old.uses:
                    inviter = invite.inviter.mention
                    invite_count = invite.uses
                    break

        self.invites_cache[guild.id] = new_invites

        member_position = guild.member_count

        embed = discord.Embed(
            title="🥗 ยินดีต้อนรับสู่เซิร์ฟเวอร์",
            description=(
                f"ยินดีต้อนรับคุณ {member.mention} เข้าสู่เซิร์ฟเวอร์ **{guild.name}**\n\n"
                f"👤 ผู้ให้คำเชิญ: {inviter}\n"
                f"🍇 ใช้ลิงก์นี้ไปแล้ว: {invite_count} ครั้ง\n"
                f"🍃 คุณคือสมาชิกคนที่ **{member_position}** ของเซิร์ฟเวอร์"
            ),
            color=discord.Color.dark_gray()
        )

        embed.set_thumbnail(url=member.display_avatar.url)
        embed.set_footer(text=f"ID: {member.id}")

        await channel.send(embed=embed)

    @app_commands.command(
        name="invitation_set",
        description="ตั้งค่าห้องเช็คคำเชิญ (ใช้ได้เฉพาะแอดมิน)"
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def invitation_set(
        self,
        interaction: discord.Interaction,
        channel: discord.TextChannel
    ):
        self.welcome_channel[interaction.guild.id] = channel.id

        embed = discord.Embed(
            title="🍇 ตั้งค่าห้องสำเร็จ",
            description=f"ห้องต้อนรับถูกตั้งเป็น {channel.mention}",
            color=discord.Color.dark_gray()
        )

        await interaction.response.send_message(embed=embed, ephemeral=True)

    @invitation_set.error
    async def invitation_set_error(self, interaction: discord.Interaction, error):
        if isinstance(error, app_commands.errors.MissingPermissions):
            await interaction.response.send_message(
                "🍅 คำสั่งนี้ใช้ได้เฉพาะแอดมิน",
                ephemeral=True
            )

async def setup(bot: commands.Bot):
    await bot.add_cog(Invitation(bot))