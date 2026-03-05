import discord
from discord.ext import commands
from discord import app_commands


class DisableExternalApps(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="disable_external_apps",
        description="ปิดการใช้แอพภายนอกของทุกห้อง"
    )
    async def disable_external_apps(self, interaction: discord.Interaction):

        if not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message(
                "🍎 ใช้ได้เฉพาะแอดมิน",
                ephemeral=True
            )

        if not interaction.guild.me.guild_permissions.manage_channels:
            return await interaction.response.send_message(
                "🌶️ บอทไม่มีสิทธิ์ Manage Channels",
                ephemeral=True
            )

        disabled = 0

        for channel in interaction.guild.channels:

            if isinstance(channel, discord.TextChannel):

                try:

                    overwrite = channel.overwrites_for(interaction.guild.default_role)
                    overwrite.use_external_apps = False

                    await channel.set_permissions(
                        interaction.guild.default_role,
                        overwrite=overwrite
                    )

                    disabled += 1

                except:
                    pass

        embed = discord.Embed(
            title="🔒 ปิดการใช้แอพภายนอก",
            description=f"ปิดสำเร็จ {disabled} ห้อง",
            color=discord.Color.red()
        )

        await interaction.response.send_message(
            embed=embed,
            ephemeral=True
        )


async def setup(bot):
    await bot.add_cog(DisableExternalApps(bot))