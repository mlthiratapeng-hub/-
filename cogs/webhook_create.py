import discord
from discord.ext import commands
from discord import app_commands

class WebhookCreate(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="webhook_create",
        description="สร้าง webhook ในห้องที่เลือก (เฉพาะเจ้าของเซิร์ฟ)"
    )
    async def webhook_create(
        self,
        interaction: discord.Interaction,
        channel: discord.TextChannel
    ):

        # ใช้ได้เฉพาะเจ้าของเซิร์ฟ
        if interaction.guild.owner_id != interaction.user.id:
            return await interaction.response.send_message(
                "❌ คำสั่งนี้ใช้ได้เฉพาะเจ้าของเซิร์ฟเวอร์",
                ephemeral=True
            )

        try:
            webhook = await channel.create_webhook(
                name=f"{interaction.guild.name} Webhook"
            )

            embed = discord.Embed(
                title="🔗 Webhook Created",
                color=discord.Color.green()
            )

            embed.add_field(
                name="📁 Channel",
                value=channel.mention,
                inline=False
            )

            embed.add_field(
                name="🔗 Webhook URL",
                value=f"```{webhook.url}```",
                inline=False
            )

            embed.set_footer(text=f"Created by {interaction.user}")
            embed.set_thumbnail(url=interaction.user.display_avatar.url)

            await interaction.response.send_message(
                embed=embed,
                ephemeral=True
            )

        except Exception as e:
            await interaction.response.send_message(
                f"❌ Error: {e}",
                ephemeral=True
            )

async def setup(bot):
    await bot.add_cog(WebhookCreate(bot))