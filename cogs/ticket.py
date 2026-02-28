import discord
from discord.ext import commands
from discord import app_commands

class CloseTicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🔒 ปิดตั๋ว", style=discord.ButtonStyle.red, custom_id="close_ticket")
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):

        if not interaction.user.guild_permissions.manage_channels:
            return await interaction.response.send_message(
                "📁 ต้องมีสิทธิ์ Manage Channels",
                ephemeral=True
            )

        await interaction.response.send_message("🔒 กำลังปิดตั๋ว...", ephemeral=True)
        await interaction.channel.delete()


class TicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🎫 เปิดตั๋ว", style=discord.ButtonStyle.green, custom_id="open_ticket")
    async def open_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):

        guild = interaction.guild
        user = interaction.user

        # เช็คว่ามีตั๋วอยู่แล้วไหม
        existing = discord.utils.get(guild.channels, name=f"ticket-{user.id}")
        if existing:
            return await interaction.response.send_message(
                f"💢 คุณมีตั๋วอยู่แล้ว: {existing.mention}",
                ephemeral=True
            )

        category = discord.utils.get(guild.categories, name="TICKETS")
        if not category:
            category = await guild.create_category("TICKETS")

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            user: discord.PermissionOverwrite(view_channel=True, send_messages=True),
            guild.me: discord.PermissionOverwrite(view_channel=True)
        }

        channel = await guild.create_text_channel(
            name=f"ticket-{user.id}",
            category=category,
            overwrites=overwrites
        )

        await channel.send(
            f"{user.mention} 🎫 ทีมงานจะมาตอบเร็ว ๆ นี้",
            view=CloseTicketView()
        )

        await interaction.response.send_message(
            f"🍀 เปิดตั๋วแล้ว: {channel.mention}",
            ephemeral=True
        )


class Ticket(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # =========================
    # /ticket
    # =========================
    @app_commands.command(name="ticket", description="สร้างปุ่มเปิดตั๋ว")
    async def ticket(self, interaction: discord.Interaction):

        if interaction.guild is None:
            return await interaction.response.send_message(
                "💢 ใช้ได้เฉพาะในเซิร์ฟเวอร์",
                ephemeral=True
            )

        if not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message(
                "💢 Admin only",
                ephemeral=True
            )

        embed = discord.Embed(
            title="🎫 ระบบ Ticket",
            description="กดปุ่มด้านล่างเพื่อเปิดตั๋ว",
            color=discord.Color.blue()
        )

        await interaction.response.send_message(
            embed=embed,
            view=TicketView()
        )


async def setup(bot: commands.Bot):
    await bot.add_cog(Ticket(bot))