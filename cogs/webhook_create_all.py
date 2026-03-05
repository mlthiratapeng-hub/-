import discord
from discord.ext import commands
from discord import app_commands

class WebhookCreateAll(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="webhook_create_all",
        description="สร้าง webhook ทุกห้องในเซิร์ฟเวอร์ (Owner only)"
    )
    async def webhook_create_all(self, interaction: discord.Interaction):

        guild = interaction.guild

        if not guild:
            return await interaction.response.send_message(
                "❌ ใช้ได้เฉพาะในเซิร์ฟเวอร์",
                ephemeral=True
            )

        # ใช้ได้เฉพาะเจ้าของเซิร์ฟ
        if interaction.user.id != guild.owner_id:
            return await interaction.response.send_message(
                "❌ คำสั่งนี้ใช้ได้เฉพาะเจ้าของเซิร์ฟเวอร์",
                ephemeral=True
            )

        await interaction.response.defer(ephemeral=True)

        created = []

        for channel in guild.text_channels:

            try:
                webhook = await channel.create_webhook(
                    name=f"{guild.name}-Webhook"
                )

                created.append((channel, webhook.url))

            except:
                pass

        if not created:

            embed = discord.Embed(
                title="❌ ไม่สามารถสร้าง Webhook ได้",
                color=discord.Color.red()
            )

            return await interaction.followup.send(
                embed=embed,
                ephemeral=True
            )

        embed = discord.Embed(
            title="🔗 Webhook Created (All Channels)",
            description=f"สร้าง Webhook ทั้งหมด {len(created)} ห้อง",
            color=discord.Color.green()
        )

        for channel, url in created[:25]:

            embed.add_field(
                name=f"📁 {channel.name}",
                value=f"```{url}```",
                inline=False
            )

        embed.set_footer(
            text=f"Requested by {interaction.user}"
        )

        embed.set_thumbnail(
            url=interaction.user.display_avatar.url
        )

        await interaction.followup.send(
            embed=embed,
            ephemeral=True
        )


async def setup(bot):
    await bot.add_cog(WebhookCreateAll(bot))