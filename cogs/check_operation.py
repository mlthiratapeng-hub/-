import discord
from discord.ext import commands, tasks
from discord import app_commands

class CheckOperation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.auto_channel_id = None
        self.auto_guild_id = None
        self.auto_report.start()

    def cog_unload(self):
        self.auto_report.cancel()

    def generate_report(self, guild: discord.Guild):
        bots = [m for m in guild.members if m.bot]

        online = []
        offline = []

        for bot in bots:
            if bot.status in [discord.Status.online, discord.Status.idle, discord.Status.dnd]:
                online.append(bot)
            else:
                offline.append(bot)

        embed = discord.Embed(
            title="📁 System | Check the Operation",
            color=discord.Color.blue()
        )

        embed.add_field(
            name="💾 บอททั้งหมด",
            value=f"{len(bots)} ตัว",
            inline=False
        )

        embed.add_field(
            name="🍃 ออนไลน์",
            value=f"{len(online)} ตัว",
            inline=True
        )

        embed.add_field(
            name="💢 ออฟไลน์",
            value=f"{len(offline)} ตัว",
            inline=True
        )

        if offline:
            names = "\n".join([f"• {b.name}" for b in offline])
            embed.add_field(
                name="⚠ บอทที่ไม่ออนไลน์",
                value=names,
                inline=False
            )

        embed.set_footer(text="อัปเดตทุก 1 ชั่วโมง")

        return embed

    @app_commands.command(name="Check the operation", description="ตรวจสอบสถานะบอทในเซิร์ฟ")
    async def check_operation(self, interaction: discord.Interaction):

        guild = interaction.guild
        embed = self.generate_report(guild)

        # บันทึกช่องสำหรับรายงานอัตโนมัติ
        self.auto_channel_id = interaction.channel.id
        self.auto_guild_id = guild.id

        await interaction.response.send_message(embed=embed)

    @tasks.loop(hours=1)
    async def auto_report(self):
        if self.auto_channel_id and self.auto_guild_id:
            guild = self.bot.get_guild(self.auto_guild_id)
            channel = guild.get_channel(self.auto_channel_id)

            if guild and channel:
                embed = self.generate_report(guild)
                await channel.send(embed=embed)

    @auto_report.before_loop
    async def before_auto(self):
        await self.bot.wait_until_ready()


async def setup(bot):
    await bot.add_cog(CheckOperation(bot))