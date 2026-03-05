import discord
from discord.ext import commands
from discord import app_commands

class Webhook(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="webhook", description="ดู webhook ของช่องนั้นสำหรับหัวดิส")
    async def webhook(self, interaction: discord.Interaction):

        # ใช้ได้เฉพาะเจ้าของเซิร์ฟ
        if interaction.guild.owner_id != interaction.user.id:
            return await interaction.response.send_message(
                "🍃 คำสั่งนี้ใช้ได้เฉพาะเจ้าของเซิร์ฟเวอร์",
                ephemeral=True
            )

        await interaction.response.defer(ephemeral=True)

        webhooks_found = []

        for channel in interaction.guild.text_channels:

            try:
                hooks = await channel.webhooks()

                for hook in hooks:
                    webhooks_found.append(
                        f"📁 {channel.name}\n"
                        f"🔗 {hook.url}\n"
                        f"👤 Owner: {hook.user}\n"
                    )

            except:
                continue

        if not webhooks_found:
            return await interaction.followup.send(
                "❌ ไม่พบ webhook ในเซิร์ฟเวอร์นี้",
                ephemeral=True
            )

        embed = discord.Embed(
            title="🔗 Webhooks ในเซิร์ฟเวอร์",
            color=discord.Color.blurple()
        )

        embed.description = "\n".join(webhooks_found[:15])

        embed.set_footer(
            text=f"Server: {interaction.guild.name}"
        )

        await interaction.followup.send(embed=embed, ephemeral=True)


async def setup(bot):
    await bot.add_cog(Webhook(bot))